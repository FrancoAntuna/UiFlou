"""FastAPI REST API for runtime camera control."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import cv2

from .camera_manager import CameraManager

app = FastAPI(title="Multicamera Streaming API", version="1.0.0")
manager: Optional[CameraManager] = None


def init_manager(camera_manager: CameraManager):
    """Initialize the global camera manager."""
    global manager
    manager = camera_manager


# --- Pydantic Models ---
class CameraConfigUpdate(BaseModel):
    fps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    enabled: Optional[bool] = None


class StatusResponse(BaseModel):
    status: str
    message: str


# --- Endpoints ---
@app.get("/api/status")
async def get_all_status():
    """Get status of all cameras."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")
    return {"cameras": manager.get_all_status()}


@app.get("/api/cameras/{camera_id}")
async def get_camera_status(camera_id: str):
    """Get status of a specific camera."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")
    status = manager.get_camera_status(camera_id)
    if not status:
        raise HTTPException(status_code=404, detail="Camera not found")
    return status


@app.post("/api/cameras/{camera_id}/config")
async def update_camera_config(camera_id: str, config: CameraConfigUpdate):
    """Update camera configuration (FPS, resolution, enabled state)."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    updates = config.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No configuration provided")

    success = manager.update_camera_config(camera_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {"status": "ok", "message": f"Camera {camera_id} config updated", "updates": updates}


@app.post("/api/cameras/{camera_id}/start")
async def start_camera(camera_id: str):
    """Start a specific camera stream."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    success = manager.start_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found or failed to start")

    return {"status": "ok", "message": f"Camera {camera_id} started"}


@app.post("/api/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """Stop a specific camera stream."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    success = manager.stop_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {"status": "ok", "message": f"Camera {camera_id} stopped"}


@app.post("/api/cameras/{camera_id}/record/start")
async def start_recording(camera_id: str):
    """Start recording for a specific camera."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    success = manager.start_recording(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {"status": "ok", "message": f"Recording started for {camera_id}"}


@app.post("/api/cameras/{camera_id}/record/stop")
async def stop_recording(camera_id: str):
    """Stop recording for a specific camera."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    success = manager.stop_recording(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recording not active")

    return {"status": "ok", "message": f"Recording stopped for {camera_id}"}


@app.post("/api/reload")
async def reload_config():
    """Hot-reload configuration from config.yaml."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    manager.reload_config()
    return {"status": "ok", "message": "Configuration reloaded"}


@app.get("/api/stream/grid")
async def stream_grid():
    """Stream grid view as MJPEG."""
    if not manager:
        raise HTTPException(status_code=503, detail="Manager not initialized")

    def generate():
        while True:
            frame = manager.get_grid_frame()
            if frame is not None:
                _, jpeg = cv2.imencode(".jpg", frame)
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )

    return StreamingResponse(
        generate(), media_type="multipart/x-mixed-replace; boundary=frame"
    )
