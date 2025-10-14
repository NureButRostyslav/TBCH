import numpy as np
from sentence_transformers import SentenceTransformer
import json

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = SentenceTransformer(_MODEL_NAME)

def text_from_image_entry(img_entry):
    parts = []
    try:
        parts.append(str(img_entry.filename))
        parts.append("uploaded by " + str(img_entry.uploader))
    except:
        pass
    try:
        md = json.loads(img_entry.metadata_json or "{}")
        # include any free-text fields if available
        if isinstance(md, dict):
            parts.extend([f"{k} {v}" for k,v in md.items()])
        else:
            parts.append(str(md))
    except:
        pass
    try:
        analysis = json.loads(img_entry.analysis_json or "{}")
        # include cluster and dominant color
        if isinstance(analysis, dict):
            if analysis.get("cluster") is not None:
                parts.append(f"cluster {analysis.get('cluster')}")
            if analysis.get("dominant_color"):
                parts.append(analysis.get("dominant_color"))
    except:
        pass
    try:
        objs = json.loads(img_entry.objects_json or "[]")
        # add object labels with confidences
        for o in objs:
            lbl = o.get("label") or ""
            conf = o.get("confidence")
            parts.append(f"{lbl} {conf:.2f}" if conf is not None else lbl)
    except:
        pass
    # fallback ensure single str
    text = " | ".join([p for p in parts if p])
    if not text:
        text = img_entry.filename or "image"
    return text

def embed_text(text):
    emb = _model.encode(text, normalize_embeddings=True)
    if isinstance(emb, np.ndarray):
        return emb
    return np.array(emb)

def embed_image_entry(img_entry):
    text = text_from_image_entry(img_entry)
    return embed_text(text)

def cosine_sim(a, b):
    if a is None or b is None or len(a)==0 or len(b)==0:
        return 0.0
    return float(np.dot(a, b))
