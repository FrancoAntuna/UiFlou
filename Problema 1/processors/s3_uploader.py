"""
Uploader de archivos a AWS S3.
Credenciales via variables de entorno: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
Bucket via config.json
"""
import os
import json
import boto3
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError


class S3Uploader:
    """Sube archivos a AWS S3."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.client = None
        self._init_client()
    
    def _load_config(self, config_path: str) -> dict:
        """Carga configuración desde JSON."""
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {"s3": {"bucket": "", "prefix": "video-processing/"}}
    
    def _init_client(self):
        """Inicializa cliente S3 con credenciales de entorno."""
        try:
            self.client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        except Exception as e:
            print(f"Warning: No se pudo inicializar S3: {e}")
            self.client = None
    
    def upload_file(self, file_path: str, key: str = None) -> bool:
        """
        Sube un archivo a S3.
        
        Args:
            file_path: Ruta local del archivo
            key: Key en S3 (opcional, usa nombre del archivo)
            
        Returns:
            True si exitoso, False si falló
        """
        if not self.client:
            print("S3 client no inicializado. Verificar credenciales.")
            return False
        
        bucket = self.config.get("s3", {}).get("bucket", "")
        if not bucket:
            print("Bucket no configurado en config.json")
            return False
        
        path = Path(file_path)
        if not path.exists():
            print(f"Archivo no encontrado: {file_path}")
            return False
        
        if key is None:
            prefix = self.config.get("s3", {}).get("prefix", "")
            key = f"{prefix}{path.name}"
        
        try:
            self.client.upload_file(str(path), bucket, key)
            print(f"Uploaded to S3: s3://{bucket}/{key}")
            return True
        except NoCredentialsError:
            print("Error: Credenciales AWS no encontradas")
            return False
        except ClientError as e:
            print(f"Error S3: {e}")
            return False
    
    def upload_directory(self, dir_path: str, pattern: str = "*.json") -> int:
        """Sube todos los archivos que coincidan con el patrón."""
        path = Path(dir_path)
        count = 0
        for file in path.glob(pattern):
            if self.upload_file(str(file)):
                count += 1
        return count
