"""Video output handler (HLS via FFmpeg or MP4 via OpenCV)."""
import os
import shutil
import subprocess
import cv2


class VideoWriter:
    def __init__(self, output_dir: str, width: int, height: int, fps: float):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.hls_path = os.path.join(output_dir, "stream.m3u8")
        self.mp4_path = os.path.join(output_dir, "output.mp4")
        
        ffmpeg = shutil.which("ffmpeg")
        
        if ffmpeg:
            print(f"FFmpeg detectado. Salida HLS: {self.hls_path}")
            self.proc = subprocess.Popen([
                ffmpeg, '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                '-s', f'{width}x{height}', '-r', str(fps), '-i', '-',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
                '-f', 'hls', '-hls_time', '2', '-hls_list_size', '5', self.hls_path
            ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.writer = None
            self.output_path = self.hls_path
        else:
            print(f"FFmpeg no encontrado. Salida MP4: {self.mp4_path}")
            self.proc = None
            self.writer = cv2.VideoWriter(
                self.mp4_path, 
                cv2.VideoWriter_fourcc(*'mp4v'), 
                fps, 
                (width, height)
            )
            self.output_path = self.mp4_path
    
    def write(self, frame):
        """Escribe un frame al video de salida."""
        if self.proc:
            try:
                self.proc.stdin.write(frame.tobytes())
            except BrokenPipeError:
                print("FFmpeg process crashed.")
                self.proc = None
        elif self.writer:
            self.writer.write(frame)
    
    def release(self):
        """Libera recursos."""
        if self.writer:
            self.writer.release()
        if self.proc:
            self.proc.stdin.close()
            self.proc.wait()
        
        print(f"Video guardado: {self.output_path}")
