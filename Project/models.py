from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=True)

class ImageEntry(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(260), nullable=False)
    uploader = db.Column(db.String(120), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    filepath = db.Column(db.String(400), nullable=False)
    metadata_json = db.Column(db.Text, default="{}")   # user provided metadata
    analysis_json = db.Column(db.Text, default="{}")   # earlier image analysis (brightness, hist, cluster)
    objects_json = db.Column(db.Text, default="[]")    # detected objects by YOLO: [{"label": "...", "confidence": 0.87}, ...]
    embedding_json = db.Column(db.Text, default="[]")  # semantic embedding for search (JSON array of floats)

    def get_metadata(self):
        try:
            return json.loads(self.metadata_json)
        except:
            return {}

    def get_analysis(self):
        try:
            return json.loads(self.analysis_json)
        except:
            return {}

    def get_objects(self):
        try:
            return json.loads(self.objects_json)
        except:
            return []

    def get_embedding(self):
        try:
            return json.loads(self.embedding_json)
        except:
            return []

class OpenEvent(db.Model):
    __tablename__ = "opens"
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(120), nullable=False)
    image_id = db.Column(db.Integer, nullable=False)
    ts = db.Column(db.DateTime, default=datetime.utcnow)

class UserPrefs(db.Model):
    """
    Persisted recommender state:
    - prefs_json: cluster counts
    - profile_embedding_json: aggregated embedding of images user opened
    - views: number of images used to build profile embedding (for incremental averaging)
    """
    __tablename__ = "userprefs"
    user = db.Column(db.String(120), primary_key=True)
    prefs_json = db.Column(db.Text, default="{}")
    profile_embedding_json = db.Column(db.Text, default="[]")
    views = db.Column(db.Integer, default=0)