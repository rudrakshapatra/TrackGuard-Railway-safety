"""
YOLOv8-based track fault detector from LiDAR point clouds.
Converts 3D point cloud to range image, runs inference.
"""
import numpy as np

FAULT_TYPES = ["track_crack", "gap", "weld_break", "alignment_deviation", "debris", "normal"]

class FaultDetector:
    def __init__(self, model_path="models/trackguard_yolo.pt"):
        self.model = None
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            print(f"[FaultDetector] YOLOv8 model loaded: {model_path}")
        except Exception as e:
            print(f"[FaultDetector] Model not found, using simulation: {e}")

    def detect(self, point_cloud_3d):
        if self.model is None:
            return self._simulate_detection(point_cloud_3d)
        
        range_image = self._to_range_image(point_cloud_3d)
        results = self.model(range_image)
        faults = []
        for box in results[0].boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            if cls < len(FAULT_TYPES) - 1 and conf > 0.70:
                faults.append({
                    "type": FAULT_TYPES[cls],
                    "confidence": round(conf, 3),
                    "distance_m": 0.5,
                })
        return faults

    def _to_range_image(self, cloud):
        img = np.zeros((64, 360), dtype=np.float32)
        for pt in cloud:
            col = int(pt["angle"]) % 360
            row = min(63, int(pt["dist"] / 100))
            img[row, col] = pt["dist"]
        return img

    def _simulate_detection(self, cloud):
        import random
        dists = [pt["dist"] for pt in cloud if 80 < pt["angle"] < 100]
        if dists and min(dists) < 900:
            return [{"type": "track_crack", "confidence": round(random.uniform(0.85, 0.96), 3),
                     "distance_m": min(dists)/1000}]
        return []
