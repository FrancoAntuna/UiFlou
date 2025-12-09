"""Pose Estimation + Tracking processor using YOLOv8-Pose."""
from ultralytics import YOLO


class PoseEstimator:
    def __init__(self, model_path: str = "yolov8n-pose.pt"):
        self.model = YOLO(model_path)
    
    def process(self, frame):
        """
        Estima poses con tracking en el frame.
        Returns: (results, poses_list)
        """
        results = self.model.track(frame, persist=True, verbose=False)[0]
        
        poses = []
        if results.keypoints is not None and results.boxes is not None:
            for i, kp in enumerate(results.keypoints.data):
                pose = {"keypoints": kp.tolist()}
                if results.boxes[i].id is not None:
                    pose["track_id"] = int(results.boxes[i].id)
                poses.append(pose)
        
        return results, poses

