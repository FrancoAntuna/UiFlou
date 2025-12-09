"""
Exportador de datos parciales cada 1 segundo.
"""
import json
import numpy as np
from datetime import datetime
from pathlib import Path


def convert_to_serializable(obj):
    """Convierte numpy types a tipos nativos de Python."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    return obj


class DataExporter:
    """Genera archivos JSON parciales cada 1 segundo."""
    
    def __init__(self, output_dir: str = "output", fps: float = 30.0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.fps = fps
        self.frame_count = 0
        self.current_second = 0
        self.second_buffer = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_frame_data(self, frame_number: int, tracks: list, angles: dict, actions: dict):
        """
        Agrega datos de un frame al buffer.
        
        Args:
            frame_number: Número de frame
            tracks: Lista de tracks [{id, bbox, keypoints}]
            angles: Dict {track_id: {angle_name: value}}
            actions: Dict {track_id: action_name}
        """
        frame_data = {
            "frame": frame_number,
            "timestamp_ms": int((frame_number / self.fps) * 1000),
            "persons": []
        }
        
        for track in tracks:
            track_id = track["id"]
            person_data = {
                "id": track_id,
                "bbox": track["bbox"].tolist() if hasattr(track["bbox"], 'tolist') else track["bbox"],
                "keypoints": track["keypoints"].tolist() if track["keypoints"] is not None else None,
                "angles": angles.get(track_id, {}),
                "action": actions.get(track_id, "unknown")
            }
            frame_data["persons"].append(person_data)
        
        self.second_buffer.append(frame_data)
        self.frame_count += 1
        
        # Exportar cada 1 segundo
        current_second = int(frame_number / self.fps)
        if current_second > self.current_second:
            self._export_second(self.current_second)
            self.current_second = current_second
            self.second_buffer = []
    
    def _export_second(self, second: int):
        """Exporta el buffer del segundo actual a JSON."""
        if not self.second_buffer:
            return
        
        filename = self.output_dir / f"{self.session_id}_second_{second:04d}.json"
        
        export_data = {
            "session_id": self.session_id,
            "second": second,
            "fps": self.fps,
            "frames": self.second_buffer
        }
        
        with open(filename, 'w') as f:
            json.dump(convert_to_serializable(export_data), f, indent=2)
        
        print(f"Exported: {filename.name}")
    
    def finalize(self):
        """Exporta datos restantes al finalizar."""
        if self.second_buffer:
            self._export_second(self.current_second)
