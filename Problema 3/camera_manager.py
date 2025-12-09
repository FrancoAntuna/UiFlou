"""Camera manager - orchestrates multiple camera streams."""
import cv2
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

from camera_stream import CameraStream, CameraConfig


class CameraManager:
    """Manages multiple camera streams with grid display and recording."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.cameras: Dict[str, CameraStream] = {}
        self.config = self._load_config()
        self._writers: Dict[str, cv2.VideoWriter] = {}
        self._init_cameras()

    def _load_config(self) -> dict:
        """Load configuration from YAML."""
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def reload_config(self):
        """Hot-reload configuration."""
        self.config = self._load_config()

    def _init_cameras(self):
        """Initialize camera streams from config."""
        for cam_cfg in self.config.get("cameras", []):
            camera_config = CameraConfig(
                id=cam_cfg["id"],
                name=cam_cfg["name"],
                source=cam_cfg["source"],
                enabled=cam_cfg.get("enabled", True),
                fps=cam_cfg.get("fps", 30),
                width=cam_cfg.get("width", 640),
                height=cam_cfg.get("height", 480),
            )
            self.cameras[camera_config.id] = CameraStream(camera_config)

    def start_all(self):
        """Start all enabled cameras."""
        for cam_id, camera in self.cameras.items():
            if camera.config.enabled:
                success = camera.start()
                print(f"[{cam_id}] Started: {success}")

    def stop_all(self):
        """Stop all cameras and writers."""
        for camera in self.cameras.values():
            camera.stop()
        for writer in self._writers.values():
            writer.release()
        self._writers.clear()

    def start_camera(self, camera_id: str) -> bool:
        """Start a specific camera."""
        if camera_id not in self.cameras:
            return False
        return self.cameras[camera_id].start()

    def stop_camera(self, camera_id: str) -> bool:
        """Stop a specific camera."""
        if camera_id not in self.cameras:
            return False
        self.cameras[camera_id].stop()
        return True

    def update_camera_config(self, camera_id: str, **kwargs) -> bool:
        """Update camera configuration."""
        if camera_id not in self.cameras:
            return False
        self.cameras[camera_id].update_config(**kwargs)
        return True

    def get_camera_status(self, camera_id: str) -> Optional[dict]:
        """Get status of a specific camera."""
        if camera_id not in self.cameras:
            return None
        return self.cameras[camera_id].to_dict()

    def get_all_status(self) -> List[dict]:
        """Get status of all cameras."""
        return [cam.to_dict() for cam in self.cameras.values()]

    def get_grid_frame(self) -> Optional[np.ndarray]:
        """Create a grid view of all active cameras."""
        frames = []
        display_cfg = self.config.get("display", {})
        grid_cols = display_cfg.get("grid_cols", 2)

        for camera in self.cameras.values():
            frame = camera.get_frame()
            if frame is not None:
                # Add camera label
                cv2.putText(
                    frame,
                    f"{camera.config.name} | {camera.status.fps_actual:.1f}fps",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                frames.append(frame)
            else:
                # Placeholder for disconnected camera
                placeholder = np.zeros(
                    (camera.config.height, camera.config.width, 3), dtype=np.uint8
                )
                cv2.putText(
                    placeholder,
                    f"{camera.config.name}: No Signal",
                    (50, camera.config.height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )
                frames.append(placeholder)

        if not frames:
            return None

        # Arrange in grid
        rows = []
        for i in range(0, len(frames), grid_cols):
            row_frames = frames[i : i + grid_cols]
            # Pad row if needed
            while len(row_frames) < grid_cols:
                row_frames.append(np.zeros_like(frames[0]))
            rows.append(np.hstack(row_frames))

        return np.vstack(rows) if rows else None

    def start_recording(self, camera_id: str) -> bool:
        """Start recording for a specific camera."""
        if camera_id not in self.cameras:
            return False

        camera = self.cameras[camera_id]
        output_cfg = self.config.get("output", {})
        base_dir = Path(output_cfg.get("base_dir", "output"))
        cam_dir = base_dir / camera_id
        cam_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = cam_dir / f"{timestamp}.mp4"

        fourcc = cv2.VideoWriter_fourcc(*output_cfg.get("codec", "mp4v"))
        self._writers[camera_id] = cv2.VideoWriter(
            str(filename),
            fourcc,
            camera.config.fps,
            (camera.config.width, camera.config.height),
        )
        return True

    def stop_recording(self, camera_id: str) -> bool:
        """Stop recording for a specific camera."""
        if camera_id in self._writers:
            self._writers[camera_id].release()
            del self._writers[camera_id]
            return True
        return False

    def write_frames(self):
        """Write current frames to active recordings."""
        for cam_id, writer in self._writers.items():
            frame = self.cameras[cam_id].get_frame()
            if frame is not None:
                writer.write(frame)
