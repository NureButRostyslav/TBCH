import os
from flask import Flask, request, jsonify, send_file
from models import db, User, ImageEntry, OpenEvent, UserPrefs
from ml_image_analyzer import ImageAnalyzer
from recommender import Recommender
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import uuid
import json
import numpy as np
from semantic_search import embed_text, embed_image_entry, text_from_image_entry, cosine_sim
from rapidfuzz import fuzz, process  # for fuzzy string matching fallback
from blockchain import Blockchain


UPLOAD_FOLDER = "storage/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///server.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

analyzer = ImageAnalyzer(n_clusters=6)
recommender = Recommender(db)
blockchain = Blockchain()

def token_auth():
    token = request.headers.get("X-Token")
    if not token:
        return None
    u = User.query.filter_by(token=token).first()
    return u

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error":"username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error":"username exists"}), 400
    uh = generate_password_hash(password)
    u = User(username=username, password_hash=uh)
    db.session.add(u)
    db.session.commit()
    return jsonify({"ok":True})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"error":"invalid"}), 401
    token = uuid.uuid4().hex
    u.token = token
    db.session.commit()
    return jsonify({"token": token})

@app.route("/upload", methods=["POST"])
def upload():
    u = token_auth()
    if not u:
        return jsonify({"error":"auth required"}), 401
    if 'file' not in request.files:
        return jsonify({"error":"file required"}), 400
    
    valid = blockchain.check_integrity()
    if not valid:
        return jsonify({"error": "Blockchain was compromised!"}), 500
    
    f = request.files['file']
    filename = secure_filename(f.filename)
    uid = uuid.uuid4().hex[:8]
    save_name = f"{uid}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, save_name)
    f.save(filepath)
    try:
        analysis = analyzer.analyze_image_file(filepath)
    except Exception as e:
        return jsonify({"error":"invalid image file", "exc": str(e)}), 400

    meta = request.form.get("metadata") or "{}"
    objs = analysis.get("objects", [])
    # build semantic embedding from textual description of the image
    class _Tmp:
        def __init__(self, filename, uploader, metadata_json, analysis_json, objects_json):
            self.filename = filename
            self.uploader = uploader
            self.metadata_json = metadata_json
            self.analysis_json = analysis_json
            self.objects_json = objects_json
    tmp = _Tmp(filename, u.username, meta, json.dumps(analysis), json.dumps(objs))
    emb = embed_image_entry(tmp)
    emb_list = emb.tolist()

    ie = ImageEntry(filename=filename, uploader=u.username, filepath=filepath,
                    metadata_json=meta, analysis_json=json.dumps(analysis),
                    objects_json=json.dumps(objs), embedding_json=json.dumps(emb_list))
    
    image_data_json = json.dumps(image_entry_to_dict(ie))
    try:
        blockchain.add_block(image_data_json)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({"error": str(e)}), 500
    
    db.session.add(ie)
    db.session.commit()

    all_images = ImageEntry.query.all()
    feats = []
    for im in all_images:
        try:
            img_pil = Image.open(im.filepath)
            feats.append(analyzer.__class__.image_to_feature(img_pil) if hasattr(analyzer.__class__, "image_to_feature") else None)
        except:
            continue
    
    return jsonify({"ok":True, "image_id": ie.id, "analysis": analysis})

def image_entry_to_dict(image_entry):
    return {
        "filename": image_entry.filename,
        "uploader": image_entry.uploader,
        "filepath": image_entry.filepath,
        "metadata_json": image_entry.metadata_json,
        "analysis_json": image_entry.analysis_json,
        "objects_json": image_entry.objects_json,
        "embedding_json": image_entry.embedding_json
    }

@app.route("/images", methods=["GET"])
def list_images():
    u = token_auth()
    if not u:
        return jsonify({"error":"auth required"}), 401
    q = request.args.get("q", "").strip()
    items = []
    
    all_images = ImageEntry.query.order_by(ImageEntry.upload_time.desc()).all()
    if not q:
        for img in all_images:
            items.append({
                "id": img.id, "filename": img.filename, "uploader": img.uploader,
                "upload_time": img.upload_time.isoformat()
            })
        return jsonify(items)

    qlow = q.lower()
    lexical_hits = []
    for img in all_images:
        combined = " ".join([img.filename or "", img.upload_time.isoformat() if img.upload_time else "", img.uploader or "", img.metadata_json or "", img.analysis_json or ""]).lower()
        if qlow in combined:
            lexical_hits.append((1.0, img))  # score 1.0 baseline for lexical hits

    fuzzy_hits = []
    names = {img.id: img.filename for img in all_images}
    
    fuzzy_top = process.extract(q, names, scorer=fuzz.WRatio, limit=10)
    fuzzy_ids = {t[2] for t in fuzzy_top if t[1] >= 60}  # keep reasonably similar matches
    for img in all_images:
        if img.id in fuzzy_ids and (qlow not in (img.filename or "").lower()):
            fuzzy_hits.append((0.75, img))

    semantic_hits = []
    try:
        q_emb = embed_text(q)
        for img in all_images:
            emb_list = img.get_embedding()
            if emb_list:
                img_emb = np.array(emb_list, dtype=float)
                sim = float(np.dot(q_emb, img_emb))
                if sim > 0.6:  # similarities threshold
                    semantic_hits.append((sim, img))
    except Exception as e:
        # embedding compute failed - skip semantic
        semantic_hits = []

    combined = {}
    for score, img in lexical_hits + fuzzy_hits + semantic_hits:
        prev = combined.get(img.id)
        if not prev or score > prev[0]:
            combined[img.id] = (score, img)
    
    sorted_items = sorted(combined.values(), key=lambda x: x[0], reverse=True)
    for score, img in sorted_items:
        items.append({
            "id": img.id,
            "filename": img.filename,
            "uploader": img.uploader,
            "upload_time": img.upload_time.isoformat(),
            "score": float(score)
        })
    return jsonify(items)

@app.route("/image/<int:image_id>/download", methods=["GET"])
def download_image(image_id):
    u = token_auth()
    if not u:
        return jsonify({"error":"auth required"}), 401
    img = ImageEntry.query.get(image_id)
    if not img:
        return jsonify({"error":"not found"}), 404
    return send_file(img.filepath, as_attachment=True, download_name=img.filename)

@app.route("/image/<int:image_id>/meta", methods=["GET"])
def image_meta(image_id):
    u = token_auth()
    if not u:
        return jsonify({"error":"auth required"}), 401
    img = ImageEntry.query.get(image_id)
    if not img:
        return jsonify({"error":"not found"}), 404
    return jsonify({
        "id": img.id,
        "filename": img.filename,
        "uploader": img.uploader,
        "upload_time": img.upload_time.isoformat(),
        "metadata": img.metadata_json,
        "analysis": img.analysis_json
    })

@app.route("/image/<int:image_id>/open", methods=["POST"])
def open_event(image_id):
    u = token_auth()
    if not u:
        return jsonify({"error":"auth required"}), 401
    img = ImageEntry.query.get(image_id)
    if not img:
        return jsonify({"error":"not found"}), 404
    oe = OpenEvent(user=u.username, image_id=image_id)
    db.session.add(oe)
    db.session.commit()
    analysis = img.get_analysis()
    cluster = analysis.get("cluster")
    recommender.increment_pref(u.username, cluster)
    try:
        emb = img.get_embedding()
        if emb:
            recommender.update_profile_embedding(u.username, np.array(emb, dtype=float))
    except Exception as e:
        print("Could not update profile embedding:", e)
    return jsonify({"ok":True})

@app.route("/recommendations", methods=["GET"])
def recommendations():
    u = token_auth()
    if not u:
        return jsonify({"error":"auth required"}), 401
    recs = recommender.recommend_for_user(u.username, max_n=3)
    return jsonify(recs)

@app.route("/blockchain/integrity", methods=["GET"])
def blockchain_integrity():
    u = token_auth()
    if not u:
        return jsonify({"error": "auth required"}), 401

    valid = blockchain.check_integrity()
    result = {"valid": valid}
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
