"""Object Detection + Tracking processor using YOLOv8."""
from ultralytics import YOLO


class ObjectDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)
        self.names = self.model.names
    
    def process(self, frame):
        """
        Detecta y trackea objetos en el frame.
        Returns: (results, detections_list)
        """
        results = self.model.track(frame, persist=True, verbose=False)[0]
        
        detections = []
        for box in results.boxes:
            det = {
                "class": self.names[int(box.cls)],
                "conf": float(box.conf),
                "bbox": box.xyxy[0].tolist()
            }
            if box.id is not None:
                det["track_id"] = int(box.id)
            detections.append(det)
        
        return results, detections

