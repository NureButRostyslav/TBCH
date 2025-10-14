import json
import numpy as np
from models import UserPrefs, db, ImageEntry, OpenEvent
from datetime import datetime
from semantic_search import cosine_sim

class Recommender:
    def __init__(self, db_session):
        self.db = db_session

    def get_prefs(self, username):
        up = UserPrefs.query.filter_by(user=username).first()
        if not up:
            return {}
        try:
            return json.loads(up.prefs_json)
        except:
            return {}

    def get_profile_embedding(self, username):
        up = UserPrefs.query.filter_by(user=username).first()
        if not up:
            return None
        try:
            arr = json.loads(up.profile_embedding_json or "[]")
            if not arr:
                return None
            return np.array(arr, dtype=float)
        except:
            return None

    def increment_pref(self, username, cluster_label):
        if cluster_label is None:
            return
        up = UserPrefs.query.filter_by(user=username).first()
        if not up:
            up = UserPrefs(user=username, prefs_json=json.dumps({}), profile_embedding_json="[]", views=0)
            db.session.add(up)
        prefs = {}
        try:
            prefs = json.loads(up.prefs_json)
        except:
            prefs = {}
        key = f"cluster_{cluster_label}"
        prefs[key] = prefs.get(key, 0) + 1
        up.prefs_json = json.dumps(prefs)
        db.session.commit()

    def update_profile_embedding(self, username, image_embedding):
        if image_embedding is None:
            return
        up = UserPrefs.query.filter_by(user=username).first()
        if not up:
            up = UserPrefs(user=username, prefs_json=json.dumps({}), profile_embedding_json=json.dumps(image_embedding.tolist()), views=1)
            db.session.add(up)
            db.session.commit()
            return
        try:
            current = json.loads(up.profile_embedding_json or "[]")
            if not current:
                # first time
                up.profile_embedding_json = json.dumps(image_embedding.tolist())
                up.views = 1
            else:
                cur = np.array(current, dtype=float)
                v = up.views or 0
                new = (cur * v + image_embedding) / (v + 1)
                up.profile_embedding_json = json.dumps(new.tolist())
                up.views = v + 1
            db.session.commit()
        except Exception as e:
            print("Failed to update profile embedding:", e)

    def recommend_for_user(self, username, max_n=10):
        prefs = self.get_prefs(username)
        pref_total = sum(prefs.values()) if prefs else 0
        profile_vec = self.get_profile_embedding(username)
        images = ImageEntry.query.all()
        scored = []
        for img in images:
            analysis = img.get_analysis()
            cluster = analysis.get("cluster")
            ckey = f"cluster_{cluster}"
            pref_score = (prefs.get(ckey, 0) / pref_total) if pref_total>0 else 0
            recency_days = (datetime.utcnow() - img.upload_time).days
            recency_boost = max(0, 1 - (recency_days / 30.0))
            opens_count = OpenEvent.query.filter_by(image_id=img.id).count()
            sem_score = 0.0
            try:
                emb = img.get_embedding()
                if emb:
                    img_emb = np.array(emb, dtype=float)
                    if profile_vec is not None:
                        sem_score = cosine_sim(profile_vec, img_emb)
            except:
                sem_score = 0.0

            score = sem_score * 2.5 + pref_score * 2.0 + recency_boost * 0.5 + min(opens_count,10)*0.05
            scored.append((score, img, sem_score))
        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for score, img, sem in scored[:max_n]:
            result.append({"id": img.id, "filename": img.filename, "score": float(score), "semantic": float(sem)})
        return result