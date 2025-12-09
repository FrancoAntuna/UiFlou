"""
Procesamiento de video: Pose Estimation + HAR + Tracking + Angles + Export + S3
Uso: python main.py [video.mp4]

Variables de entorno para S3:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION (default: us-east-1)
"""
import sys
import cv2
import shutil
from pathlib import Path
from processors.pose_tracker import PoseTracker
from processors.har_detector import HARDetector
from processors.angle_calculator import AngleCalculator
from processors.data_exporter import DataExporter
from processors.video_exporter import VideoExporter
from processors.s3_uploader import S3Uploader


OUTPUT_DIR = "output"
VIDEO_OUTPUT_DIR = "video_outputs"


def get_video_source():
    """Retorna la fuente de video (archivo o webcam)."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return 0  # webcam


def cleanup_outputs(confirm: bool = True):
    """Limpia los JSONs de salida (los videos nunca se eliminan)."""
    output_path = Path(OUTPUT_DIR)
    
    json_files = list(output_path.glob("*.json")) if output_path.exists() else []
    
    if not json_files:
        return
    
    if confirm:
        print(f"\nSe encontraron {len(json_files)} JSONs en '{OUTPUT_DIR}/'")
        response = input("¿Desea limpiar los JSONs? (s/n): ").strip().lower()
        if response != 's':
            print("Manteniendo archivos existentes.\n")
            return
    
    for f in json_files:
        f.unlink()
    
    if confirm:
        print("JSONs eliminados.\n")



def main():
    # Preguntar por limpieza de JSONs antes de procesar
    cleanup_outputs()
    
    source = get_video_source()
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"Error: No se pudo abrir la fuente de video: {source}")
        sys.exit(1)
    
    # Obtener FPS del video
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    
    # Inicializar procesadores
    pose_tracker = PoseTracker()
    har_detector = HARDetector(fps=fps)
    angle_calculator = AngleCalculator()
    data_exporter = DataExporter(output_dir=OUTPUT_DIR, fps=fps)
    video_exporter = VideoExporter(output_dir=VIDEO_OUTPUT_DIR, fps=fps)
    s3_uploader = S3Uploader()
    
    window_name = "Video Processing"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    frame_number = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Procesar pose + tracking
        frame, tracks = pose_tracker.process(frame)
        
        # Calcular ángulos por persona
        angles = {}
        for track in tracks:
            angles[track["id"]] = angle_calculator.calculate(track["keypoints"])
        
        # Procesar HAR
        frame, actions = har_detector.process(frame, tracks)
        
        # Exportar datos cada 1 segundo
        data_exporter.add_frame_data(frame_number, tracks, angles, actions)
        
        # Escribir frame al video de salida
        video_exporter.write_frame(frame)
        
        cv2.imshow(window_name, frame)
        frame_number += 1
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Finalizar exportación
    data_exporter.finalize()
    video_path = video_exporter.finalize()
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Procesados {frame_number} frames")
    
    # Subir a S3
    print("\nSubiendo a S3...")
    if video_path:
        s3_uploader.upload_file(video_path)
    s3_uploader.upload_directory(OUTPUT_DIR, "*.json")
    
    print("Proceso completado.")
    
    # Limpieza post-ejecución (solo JSONs, videos se mantienen)
    response = input("\n¿Desea eliminar los JSONs locales después de subir a S3? (s/n): ").strip().lower()
    if response == 's':
        cleanup_outputs(confirm=False)
        print("JSONs locales eliminados.")


if __name__ == "__main__":
    main()

