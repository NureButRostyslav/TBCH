from PIL import Image
import numpy as np
import os
import pickle
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

MODEL_PATH = "image_cluster_kmeans.pkl"

from ultralytics import YOLO

class ImageAnalyzer:
    def __init__(self, 
                 n_clusters=6, 
                 yolo_model_name="yolo11n.pt",  # default YOLO11 nano
                 conf_thresh=0.25,
                 img_size=640):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.scaler = StandardScaler()
        self.conf_thresh = conf_thresh
        self.img_size = img_size

        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.kmeans = data.get("kmeans")
                    self.scaler = data.get("scaler", StandardScaler())
            except Exception as e:
                print("Couldn't load clustering model:", e)

        try:
            self.yolo = YOLO(yolo_model_name)
        except Exception as e:
            print(f"Failed to load YOLO11 model {yolo_model_name}: {e}")
            self.yolo = None

    def fit(self, features):
        self.scaler = StandardScaler().fit(features)
        Xs = self.scaler.transform(features)
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=0).fit(Xs)
        self._save()

    def predict(self, feat):
        if self.kmeans is None:
            return None
        X = self.scaler.transform(feat.reshape(1, -1))
        return int(self.kmeans.predict(X)[0])

    def _save(self):
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump({"kmeans": self.kmeans, "scaler": self.scaler}, f)
        except Exception as e:
            print("Error saving clustering model:", e)

    def detect_objects(self, filepath):
        if self.yolo is None:
            return []

        try:
            results = self.yolo(filepath, imgsz=self.img_size, conf=self.conf_thresh)
            if not results:
                return []
            r = results[0]
            names = getattr(r, "names", None)
            boxes = getattr(r, "boxes", None)
            if boxes is None or not hasattr(boxes, "data"):
                return []

            arr = boxes.data.cpu().numpy() if hasattr(boxes.data, "cpu") else np.array(boxes.data)
            objs = []
            for b in arr:
                # b format is like [x1, y1, x2, y2, conf, cls]
                conf = float(b[4])
                cls = int(b[5])
                label = names.get(cls, str(cls)) if names is not None else str(cls)
                objs.append({"label": label, "confidence": conf})
            return objs

        except Exception as e:
            print("YOLO11 detection failed:", e)
            return []

    @staticmethod
    def image_to_feature(img: Image.Image, hist_bins=8):
        img = img.convert("RGB").resize((128, 128))
        arr = np.array(img) / 255.0
        mean_rgb = arr.mean(axis=(0,1)).tolist()
        brightness = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]).mean()
        hist = []
        for c in range(3):
            h, _ = np.histogram(arr[:,:,c].flatten(), bins=hist_bins, range=(0,1))
            s = h.sum()
            if s == 0:
                hist.extend([0.0]*hist_bins)
            else:
                hist.extend((h / s).tolist())
        feat = np.array([brightness] + mean_rgb + hist)
        return feat

    def analyze_image_file(self, filepath):
        try:
            pil = Image.open(filepath).convert("RGB")
        except Exception as e:
            raise Exception(f"Cannot open image: {e}")

        feat = self.image_to_feature(pil)
        mean_rgb = feat[1:4].tolist()
        dom_color = self._dominant_color(mean_rgb)
        brightness = float(feat[0])
        hist = feat[4:].tolist()
        cluster = self.predict(feat) if self.kmeans is not None else None
        objects = self.detect_objects(filepath)

        return {
            "dominant_color": dom_color,
            "brightness": brightness,
            "histogram": hist,
            "cluster": cluster,
            "objects": objects
        }

    @staticmethod
    def _dominant_color(mean_rgb):
        r, g, b = mean_rgb
        if r > 0.6 and r > g+0.05 and r > b+0.05:
            return "red-ish"
        if g > 0.6 and g > r+0.05 and g > b+0.05:
            return "green-ish"
        if b > 0.6 and b > r+0.05 and b > g+0.05:
            return "blue-ish"
        if r > 0.4 and g > 0.4 and b > 0.4:
            return "light"
        if r < 0.3 and g < 0.3 and b < 0.3:
            return "dark"
        return "mixed"
