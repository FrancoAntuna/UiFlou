"""Main entry point for multicamera streaming system."""
import cv2
import threading
import uvicorn
import argparse
from pathlib import Path

from processors.camera_manager import CameraManager
from processors.api import app, init_manager


def run_display(manager: CameraManager, display_cfg: dict):
    """Run OpenCV display loop in main thread."""
    window_name = display_cfg.get("window_name", "Multicamera Stream")
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("[Display] Press 'q' to quit, 'r' to reload config")

    while True:
        grid_frame = manager.get_grid_frame()
        if grid_frame is not None:
            cv2.imshow(window_name, grid_frame)

        # Write frames if recording
        manager.write_frames()

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            manager.reload_config()
            print("[Config] Reloaded")

    cv2.destroyAllWindows()


def run_api(host: str, port: int):
    """Run FastAPI server."""
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="Multicamera Streaming System")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--no-display", action="store_true", help="Disable OpenCV display")
    parser.add_argument("--no-api", action="store_true", help="Disable REST API")
    args = parser.parse_args()

    # Initialize manager
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[Error] Config file not found: {config_path}")
        return

    manager = CameraManager(str(config_path))
    init_manager(manager)

    # Start cameras
    print("[System] Starting cameras...")
    manager.start_all()

    # Start API server in background thread
    if not args.no_api:
        server_cfg = manager.config.get("server", {})
        api_thread = threading.Thread(
            target=run_api,
            args=(server_cfg.get("host", "0.0.0.0"), server_cfg.get("port", 8000)),
            daemon=True,
        )
        api_thread.start()
        print(f"[API] Server running at http://{server_cfg.get('host', '0.0.0.0')}:{server_cfg.get('port', 8000)}")
        print("[API] Docs available at /docs")

    # Run display loop (or wait indefinitely if no display)
    try:
        display_cfg = manager.config.get("display", {})
        if not args.no_display and display_cfg.get("enabled", True):
            run_display(manager, display_cfg)
        else:
            print("[System] Running in headless mode. Press Ctrl+C to stop.")
            threading.Event().wait()
    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
    finally:
        manager.stop_all()
        print("[System] Stopped")


if __name__ == "__main__":
    main()
