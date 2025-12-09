"""Individual camera stream handler."""
import cv2
import threading
import time
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class CameraConfig:
    id: str
    name: str
    source: str | int
    enabled: bool = True
    fps: int = 30
    width: int = 640
    height: int = 480


@dataclass
class CameraStatus:
    id: str
    connected: bool = False
    fps_actual: float = 0.0
    frame_count: int = 0
    last_error: Optional[str] = None


class CameraStream:
    """Handles individual RTSP/webcam stream with threading."""

    def __init__(self, config: CameraConfig):
        self.config = config
        self.status = CameraStatus(id=config.id)
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._fps_counter = 0
        self._fps_time = time.time()

    def start(self) -> bool:
        """Start the camera stream."""
        if self._running:
            return True

        self._cap = cv2.VideoCapture(self.config.source)
        if not self._cap.isOpened():
            self.status.last_error = f"Cannot open source: {self.config.source}"
            self.status.connected = False
            return False

        # Configure capture
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._running = True
        self.status.connected = True
        self.status.last_error = None
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop the camera stream."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        self.status.connected = False

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame (thread-safe)."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def update_config(self, **kwargs):
        """Update camera configuration dynamically."""
        was_running = self._running
        if was_running:
            self.stop()

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        if was_running and self.config.enabled:
            self.start()

    def _capture_loop(self):
        """Background thread for frame capture."""
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                self.status.last_error = "Frame read failed"
                time.sleep(0.1)
                continue

            # Resize if needed
            if frame.shape[1] != self.config.width or frame.shape[0] != self.config.height:
                frame = cv2.resize(frame, (self.config.width, self.config.height))

            with self._lock:
                self._frame = frame

            # Update stats
            self.status.frame_count += 1
            self._fps_counter += 1
            now = time.time()
            if now - self._fps_time >= 1.0:
                self.status.fps_actual = self._fps_counter / (now - self._fps_time)
                self._fps_counter = 0
                self._fps_time = now

            # Rate limiting
            time.sleep(1.0 / self.config.fps)

    def to_dict(self) -> dict:
        """Serialize camera state for API."""
        return {
            "config": {
                "id": self.config.id,
                "name": self.config.name,
                "source": str(self.config.source),
                "enabled": self.config.enabled,
                "fps": self.config.fps,
                "width": self.config.width,
                "height": self.config.height,
            },
            "status": {
                "connected": self.status.connected,
                "fps_actual": round(self.status.fps_actual, 2),
                "frame_count": self.status.frame_count,
                "last_error": self.status.last_error,
            },
        }
