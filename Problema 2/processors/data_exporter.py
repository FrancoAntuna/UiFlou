"""Data exporter for JSON/JSONL output."""
import os
import json
import time
from pathlib import Path


class DataExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.jsonl_path = os.path.join(output_dir, "data.jsonl")
        self.file = open(self.jsonl_path, 'w')
    
    def write(self, frame_id: int, detections: list, poses: list):
        """Escribe un registro al archivo JSONL."""
        record = {
            "ts": time.time(),
            "frame": frame_id,
            "detections": detections,
            "poses": poses
        }
        self.file.write(json.dumps(record) + "\n")
    
    def close(self):
        """Cierra el archivo."""
        self.file.close()
        print(f"Datos guardados: {self.jsonl_path}")
    
    @staticmethod
    def cleanup(output_dir: str, confirm: bool = True):
        """Limpia los JSONs de salida."""
        output_path = Path(output_dir)
        json_files = list(output_path.glob("*.json")) + list(output_path.glob("*.jsonl"))
        
        if not json_files:
            return
        
        if confirm:
            print(f"\nSe encontraron {len(json_files)} archivos JSON en '{output_dir}/'")
            response = input("¿Desea limpiarlos? (s/n): ").strip().lower()
            if response != 's':
                print("Manteniendo archivos existentes.\n")
                return
        
        for f in json_files:
            f.unlink()
        
        if confirm:
            print("Archivos JSON eliminados.\n")
