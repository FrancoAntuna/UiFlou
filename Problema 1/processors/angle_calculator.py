"""
Cálculo de ángulos corporales a partir de keypoints.
"""
import numpy as np


class AngleCalculator:
    """Calcula ángulos articulares desde keypoints COCO."""
    
    # Índices COCO
    KP = {
        "nose": 0,
        "left_shoulder": 5, "right_shoulder": 6,
        "left_elbow": 7, "right_elbow": 8,
        "left_wrist": 9, "right_wrist": 10,
        "left_hip": 11, "right_hip": 12,
        "left_knee": 13, "right_knee": 14,
        "left_ankle": 15, "right_ankle": 16
    }
    
    # Definición de ángulos: (punto1, vértice, punto2)
    ANGLE_DEFINITIONS = {
        "left_elbow": ("left_shoulder", "left_elbow", "left_wrist"),
        "right_elbow": ("right_shoulder", "right_elbow", "right_wrist"),
        "left_shoulder": ("left_elbow", "left_shoulder", "left_hip"),
        "right_shoulder": ("right_elbow", "right_shoulder", "right_hip"),
        "left_hip": ("left_shoulder", "left_hip", "left_knee"),
        "right_hip": ("right_shoulder", "right_hip", "right_knee"),
        "left_knee": ("left_hip", "left_knee", "left_ankle"),
        "right_knee": ("right_hip", "right_knee", "right_ankle"),
    }
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
    
    def _calculate_angle(self, p1: np.ndarray, vertex: np.ndarray, p2: np.ndarray) -> float:
        """Calcula ángulo en el vértice formado por p1-vertex-p2."""
        v1 = p1[:2] - vertex[:2]
        v2 = p2[:2] - vertex[:2]
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))
        
        return round(angle, 1)
    
    def calculate(self, keypoints: np.ndarray) -> dict:
        """
        Calcula todos los ángulos corporales.
        
        Args:
            keypoints: Array (17, 3) con [x, y, confidence]
            
        Returns:
            Dict con ángulos {nombre: valor_en_grados} o None si no hay confianza
        """
        if keypoints is None or len(keypoints) < 17:
            return {}
        
        angles = {}
        
        for angle_name, (p1_name, vertex_name, p2_name) in self.ANGLE_DEFINITIONS.items():
            p1 = keypoints[self.KP[p1_name]]
            vertex = keypoints[self.KP[vertex_name]]
            p2 = keypoints[self.KP[p2_name]]
            
            # Verificar confianza
            if p1[2] < self.min_confidence or vertex[2] < self.min_confidence or p2[2] < self.min_confidence:
                angles[angle_name] = None
                continue
            
            angles[angle_name] = self._calculate_angle(p1, vertex, p2)
        
        return angles
