"""
Pose Estimation + Tracking usando YOLOv8-pose con BoT-SORT integrado.
"""
from ultralytics import YOLO
import cv2


class PoseTracker:
    def __init__(self, model_name: str = "yolov8n-pose.pt"):
        self.model = YOLO(model_name)
    
    def process(self, frame):
        """
        Procesa un frame para detectar poses y trackear personas.
        
        Returns:
            frame: Frame con anotaciones
            tracks: Lista de dicts con {id, bbox, keypoints}
        """
        # track=True activa BoT-SORT internamente
        results = self.model.track(frame, persist=True, verbose=False)
        
        tracks = []
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes
            keypoints = results[0].keypoints
            
            for i, box in enumerate(boxes):
                track_id = int(box.id[0])
                bbox = box.xyxy[0].cpu().numpy()
                kpts = keypoints[i].data[0].cpu().numpy() if keypoints else None
                
                tracks.append({
                    "id": track_id,
                    "bbox": bbox,
                    "keypoints": kpts
                })
                
                # Dibujar ID
                x1, y1 = int(bbox[0]), int(bbox[1])
                cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Dibujar poses (YOLO ya lo hace, pero lo hacemos explícito)
        annotated = results[0].plot()
        
        return annotated, tracks
