"""
Exportador de video procesado a MP4.
"""
import cv2
from pathlib import Path
from datetime import datetime


class VideoExporter:
    """Graba el video procesado a archivo MP4."""
    
    def __init__(self, output_dir: str = "output", fps: float = 30.0, frame_size: tuple = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.fps = fps
        self.frame_size = frame_size
        self.writer = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = None
    
    def _init_writer(self, frame):
        """Inicializa el writer con el tamaño del primer frame."""
        if self.frame_size is None:
            h, w = frame.shape[:2]
            self.frame_size = (w, h)
        
        self.output_path = self.output_dir / f"{self.session_id}_processed.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            self.frame_size
        )
    
    def write_frame(self, frame):
        """Escribe un frame al video."""
        if self.writer is None:
            self._init_writer(frame)
        
        # Asegurar tamaño correcto
        if frame.shape[1] != self.frame_size[0] or frame.shape[0] != self.frame_size[1]:
            frame = cv2.resize(frame, self.frame_size)
        
        self.writer.write(frame)
    
    def finalize(self) -> str:
        """Cierra el writer y retorna la ruta del archivo."""
        if self.writer:
            self.writer.release()
            print(f"Video saved: {self.output_path}")
            return str(self.output_path)
        return None
