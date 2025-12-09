"""Object Detection + Tracking processor using YOLOv8."""
from ultralytics import YOLO


class ObjectDetector:
    # Excluir clase 0 (person) ya que el PoseEstimator ya detecta personas
    EXCLUDE_CLASSES = [0]  # 0 = person
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)
        self.names = self.model.names
        # Clases a detectar (todas excepto las excluidas)
        self.classes = [i for i in self.names.keys() if i not in self.EXCLUDE_CLASSES]
    
    def process(self, frame):
        """
        Detecta y trackea objetos en el frame (excluyendo personas).
        Returns: (results, detections_list)
        """
        results = self.model.track(frame, persist=True, verbose=False, classes=self.classes)[0]
        
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

