"""
Human Action Recognition (HAR) con ventana temporal de 9 segundos.
"""
import numpy as np
import cv2
from collections import deque


class HARDetector:
    """
    HAR basado en análisis temporal de keypoints.
    Usa ventana de 9 segundos para clasificación de acciones.
    """
    
    # Índices de keypoints COCO (YOLOv8-pose)
    KEYPOINTS = {
        "nose": 0,
        "left_eye": 1, "right_eye": 2,
        "left_ear": 3, "right_ear": 4,
        "left_shoulder": 5, "right_shoulder": 6,
        "left_elbow": 7, "right_elbow": 8,
        "left_wrist": 9, "right_wrist": 10,
        "left_hip": 11, "right_hip": 12,
        "left_knee": 13, "right_knee": 14,
        "left_ankle": 15, "right_ankle": 16
    }
    
    def __init__(self, fps: float = 30.0, window_seconds: float = 9.0):
        self.fps = fps
        self.window_size = int(fps * window_seconds)  # 9 segundos de buffer
        # Buffer por track_id: deque de keypoints
        self.pose_buffers = {}
    
    def _add_to_buffer(self, track_id: int, keypoints: np.ndarray):
        """Agrega keypoints al buffer temporal del track."""
        if track_id not in self.pose_buffers:
            self.pose_buffers[track_id] = deque(maxlen=self.window_size)
        self.pose_buffers[track_id].append(keypoints)
    
    def _analyze_temporal(self, track_id: int) -> dict:
        """Analiza el buffer temporal para extraer features."""
        if track_id not in self.pose_buffers:
            return {}
        
        buffer = list(self.pose_buffers[track_id])
        if len(buffer) < 10:  # Mínimo de frames para análisis
            return {"buffer_frames": len(buffer)}
        
        # Calcular movimiento promedio de muñecas
        wrist_movements = []
        for i in range(1, len(buffer)):
            if buffer[i] is not None and buffer[i-1] is not None:
                l_wrist_curr = buffer[i][self.KEYPOINTS["left_wrist"]][:2]
                l_wrist_prev = buffer[i-1][self.KEYPOINTS["left_wrist"]][:2]
                movement = np.linalg.norm(l_wrist_curr - l_wrist_prev)
                wrist_movements.append(movement)
        
        avg_movement = np.mean(wrist_movements) if wrist_movements else 0
        
        return {
            "buffer_frames": len(buffer),
            "avg_wrist_movement": round(avg_movement, 2),
            "is_moving": avg_movement > 5.0
        }
    
    def _classify_action(self, keypoints: np.ndarray, temporal_info: dict) -> str:
        """Clasificación basada en geometría + información temporal."""
        if keypoints is None or len(keypoints) < 17:
            return "unknown"
        
        # Extraer puntos clave
        l_wrist = keypoints[self.KEYPOINTS["left_wrist"]]
        r_wrist = keypoints[self.KEYPOINTS["right_wrist"]]
        l_shoulder = keypoints[self.KEYPOINTS["left_shoulder"]]
        r_shoulder = keypoints[self.KEYPOINTS["right_shoulder"]]
        l_hip = keypoints[self.KEYPOINTS["left_hip"]]
        r_hip = keypoints[self.KEYPOINTS["right_hip"]]
        l_knee = keypoints[self.KEYPOINTS["left_knee"]]
        r_knee = keypoints[self.KEYPOINTS["right_knee"]]
        l_ankle = keypoints[self.KEYPOINTS["left_ankle"]]
        r_ankle = keypoints[self.KEYPOINTS["right_ankle"]]
        
        min_conf = 0.5
        
        # Verificar si faltan ambas piernas (rodillas + tobillos)
        left_leg_missing = l_knee[2] < min_conf and l_ankle[2] < min_conf
        right_leg_missing = r_knee[2] < min_conf and r_ankle[2] < min_conf
        if left_leg_missing and right_leg_missing:
            return "unknown"
        
        # Verificar si falta todo el torso (hombros + caderas)
        torso_missing = (l_shoulder[2] < min_conf and r_shoulder[2] < min_conf and 
                        l_hip[2] < min_conf and r_hip[2] < min_conf)
        if torso_missing:
            return "unknown"
        
        # Verificar confianza mínima de hombros para clasificación
        if l_shoulder[2] < min_conf or r_shoulder[2] < min_conf:
            return "unknown"
        
        shoulder_y = (l_shoulder[1] + r_shoulder[1]) / 2
        hip_y = (l_hip[1] + r_hip[1]) / 2
        body_height = abs(hip_y - shoulder_y)
        
        # Clasificación con contexto temporal
        is_moving = temporal_info.get("is_moving", False)
        
        # Brazos levantados
        if l_wrist[2] > 0.5 and r_wrist[2] > 0.5:
            if l_wrist[1] < l_shoulder[1] and r_wrist[1] < r_shoulder[1]:
                return "waving" if is_moving else "hands_up"
        
        # Sentado
        if body_height < 50:
            return "sitting"
        
        # De pie con movimiento
        if is_moving:
            return "walking"
        
        return "standing"
    
    def process(self, frame, tracks: list):
        """
        Procesa tracks para detectar acciones con contexto temporal.
        
        Returns:
            frame: Frame con anotaciones de acción
            actions: Dict {track_id: action}
        """
        actions = {}
        
        for track in tracks:
            track_id = track["id"]
            keypoints = track["keypoints"]
            
            # Agregar al buffer temporal
            self._add_to_buffer(track_id, keypoints)
            
            # Analizar ventana temporal
            temporal_info = self._analyze_temporal(track_id)
            
            # Clasificar con contexto
            action = self._classify_action(keypoints, temporal_info)
            actions[track_id] = action
            
            # Anotar acción en frame con fondo para mejor visibilidad
            bbox = track["bbox"]
            x1, y1 = int(bbox[0]), int(bbox[1])
            label = f"{action}"
            
            # Fondo para el texto
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (x1, y1 - 50), (x1 + w + 10, y1 - 25), (0, 0, 0), -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return frame, actions
