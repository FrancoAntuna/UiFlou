"""
Problema 2: RTSP Stream Processing - Pose Estimation + Object Detection
Estructura modular con procesadores separados.
"""
import cv2
import argparse
from processors import ObjectDetector, PoseEstimator, VideoWriter, DataExporter


OUTPUT_DIR = "output"
VIDEO_OUTPUT_DIR = "video_outputs"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="RTSP URL or video file (default: webcam)", default=None)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--video-output-dir", default=VIDEO_OUTPUT_DIR)
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip cleanup prompt")
    args = parser.parse_args()

    # Pre-ejecución: cleanup con confirmación
    if not args.no_cleanup:
        DataExporter.cleanup(args.output_dir)
    
    # Video source
    source = args.source if args.source else 0
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: No se pudo abrir: {source}")
        return
    
    print(f"Fuente: {source if args.source else 'Webcam'}")
    
    w, h = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"Resolución: {w}x{h}, FPS: {fps}")
    
    # Inicializar procesadores
    detector = ObjectDetector()
    pose_estimator = PoseEstimator()
    video_writer = VideoWriter(args.video_output_dir, w, h, fps)
    data_exporter = DataExporter(args.output_dir)
    
    # Window config
    window_name = "RTSP Processing"
    if not args.no_display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
    
    frame_id = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Procesamiento
            results_det, detections = detector.process(frame)
            results_pose, poses = pose_estimator.process(frame)
            
            # Anotación: detección + pose
            annotated = results_det.plot()
            annotated = results_pose.plot(img=annotated)
            
            # Exportar datos y video
            data_exporter.write(frame_id, detections, poses)
            video_writer.write(annotated)
            
            if not args.no_display:
                cv2.imshow(window_name, annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            frame_id += 1
            if frame_id % 30 == 0:
                print(f"Procesados: {frame_id} frames", end='\r')

    except KeyboardInterrupt:
        print("\nInterrumpido por usuario.")
    finally:
        cap.release()
        data_exporter.close()
        video_writer.release()
        cv2.destroyAllWindows()
        print(f"\nProcesados {frame_id} frames")
    
    # Post-ejecución: cleanup opcional
    if not args.no_cleanup:
        response = input("\n¿Eliminar JSONs locales? (s/n): ").strip().lower()
        if response == 's':
            DataExporter.cleanup(args.output_dir, confirm=False)
            print("JSONs eliminados.")


if __name__ == "__main__":
    main()
