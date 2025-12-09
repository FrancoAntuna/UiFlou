"""
Launcher GUI - Gestor de problemas de visión por computadora
Ejecutar: python launcher.py
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import sys
import os
from pathlib import Path


class ProblemLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Problem Launcher")
        self.root.geometry("420x480")
        self.root.resizable(False, False)
        
        self.selected_video = None
        self.root.configure(bg="#1e1e2e")
        self._setup_ui()
    
    def _setup_ui(self):
        title = tk.Label(
            self.root, text="🎥 Problem Launcher",
            font=("Segoe UI", 16, "bold"), bg="#1e1e2e", fg="#cdd6f4"
        )
        title.pack(pady=15)
        
        btn_style = {
            "font": ("Segoe UI", 11), "bg": "#313244", "fg": "#cdd6f4",
            "activebackground": "#45475a", "activeforeground": "#cdd6f4",
            "relief": "flat", "cursor": "hand2", "width": 35, "height": 2
        }
        
        # === Selector de video ===
        video_frame = tk.Frame(self.root, bg="#1e1e2e")
        video_frame.pack(pady=10, fill="x", padx=30)
        
        btn_select = tk.Button(
            video_frame, text="📂 Seleccionar Video MP4",
            command=self._select_video, **btn_style
        )
        btn_select.pack(pady=5)
        
        self.video_label = tk.Label(
            video_frame, text="⚠️ Sin video → usará webcam",
            font=("Segoe UI", 9), bg="#1e1e2e", fg="#f9e2af"
        )
        self.video_label.pack(pady=5)
        
        # Separador
        tk.Frame(self.root, height=2, bg="#45475a").pack(fill="x", padx=30, pady=10)
        
        # === Botones de problemas ===
        btn_frame = tk.Frame(self.root, bg="#1e1e2e")
        btn_frame.pack(pady=5, fill="x", padx=30)
        
        tk.Button(
            btn_frame, text="📹 Problema 1: Pose + HAR + Tracking",
            command=self._run_problema1, **btn_style
        ).pack(pady=6)
        
        tk.Button(
            btn_frame, text="🔍 Problema 2: RTSP Detection",
            command=self._run_problema2, **btn_style
        ).pack(pady=6)
        
        tk.Button(
            btn_frame, text="📷 Problema 3: Multicamera Stream",
            command=self._run_problema3, **btn_style
        ).pack(pady=6)
        
        tk.Button(
            btn_frame, text="🤖 Problema 4: Agente Simple",
            command=self._run_problema4, **btn_style
        ).pack(pady=6)
        
        # Separador
        tk.Frame(self.root, height=2, bg="#45475a").pack(fill="x", padx=30, pady=10)
        
        tk.Label(
            self.root, text="P3 usa config.yaml | P4 usa webcam directamente",
            font=("Segoe UI", 9), bg="#1e1e2e", fg="#6c7086"
        ).pack(pady=5)
    
    def _select_video(self):
        """Abre diálogo para seleccionar video MP4."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar video",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            initialdir=str(Path(__file__).parent)
        )
        if file_path:
            self.selected_video = file_path
            filename = Path(file_path).name
            self.video_label.config(text=f"✅ {filename}", fg="#a6e3a1")
        else:
            self.selected_video = None
            self.video_label.config(text="⚠️ Sin video → usará webcam", fg="#f9e2af")
    
    def _run_process(self, cwd: str, args: list):
        """Ejecuta un proceso hijo y espera a que termine."""
        self.root.withdraw()
        try:
            process = subprocess.Popen(
                [sys.executable] + args, cwd=cwd,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            process.wait()
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar: {e}")
        finally:
            self.root.deiconify()
    
    def _run_problema1(self):
        """Ejecuta Problema 1 (video o webcam)."""
        problema_dir = Path(__file__).parent / "Problema 1"
        args = ["main.py"]
        if self.selected_video:
            args.append(self.selected_video)
        self._run_process(str(problema_dir), args)
    
    def _run_problema2(self):
        """Ejecuta Problema 2 (video o webcam)."""
        problema_dir = Path(__file__).parent / "Problema 2"
        args = ["main.py"]
        if self.selected_video:
            args.extend(["--source", self.selected_video])
        self._run_process(str(problema_dir), args)
    
    def _run_problema3(self):
        """Ejecuta Problema 3 (usa config.yaml por defecto)."""
        problema_dir = Path(__file__).parent / "Problema 3"
        self._run_process(str(problema_dir), ["main.py"])
    
    def _run_problema4(self):
        """Ejecuta Problema 4 (agente simple, solo webcam)."""
        problema_dir = Path(__file__).parent / "Problema 4"
        self._run_process(str(problema_dir), ["simple_agent.py"])
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ProblemLauncher().run()
