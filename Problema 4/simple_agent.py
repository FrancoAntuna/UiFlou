"""
Agente Multi-Agente con Ray para Puesto de Trabajo (Agujereadora)
==================================================================
Arquitectura distribuida usando Ray Actors:
- HandAgent: Detecta manos (MediaPipe)
- PoseAgent: Detecta pose corporal (MediaPipe)
- ObjectAgent: Detecta objetos (YOLO)

Uso: python simple_agent.py
"""

import cv2
import ray
import numpy as np
import mediapipe as mp
from ultralytics import YOLO


@ray.remote
class HandAgent:
    """Agente para detección de manos."""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
    
    def detect(self, frame):
        """Detecta manos y retorna landmarks."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        
        hand_landmarks_list = []
        hand_data = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                hand_landmarks_list.append(hand_landmarks)
                hand_data.append({
                    'type': handedness.classification[0].label,
                    'confidence': handedness.classification[0].score
                })
        
        return hand_landmarks_list, hand_data


@ray.remote
class PoseAgent:
    """Agente para detección de pose."""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7)
    
    def detect(self, frame):
        """Detecta pose y retorna landmarks."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        
        pose_landmarks = None
        if results.pose_landmarks:
            pose_landmarks = results.pose_landmarks
        
        return pose_landmarks


@ray.remote
class ObjectAgent:
    """Agente para detección de objetos."""
    
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
    
    def detect(self, frame):
        """Detecta objetos y retorna datos con bboxes."""
        results = self.model(frame, verbose=False)[0]
        
        objects = []
        for box in results.boxes:
            confidence = float(box.conf[0])
            if confidence > 0.5:
                class_id = int(box.cls[0])
                class_name = results.names[class_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                objects.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': (x1, y1, x2, y2)
                })
        
        return objects


def check_safety_rules(hands_data, pose_landmarks, objects):
    """Verifica reglas de seguridad simples."""
    alerts = []
    
    if hands_data:
        alerts.append(f"✋ {len(hands_data)} mano(s) detectada(s)")
    
    if pose_landmarks:
        alerts.append("👤 Operador detectado en posición")
    else:
        alerts.append("⚠️ Operador no visible")
    
    if objects:
        obj_names = [o['class'] for o in objects]
        alerts.append(f"📦 Objetos: {', '.join(set(obj_names))}")
    
    return alerts


def main():
    """Función principal del agente."""
    print("=" * 50)
    print("AGENTE RAY - PUESTO DE TRABAJO")
    print("=" * 50)
    print("Presiona 'q' para salir\n")
    
    # Inicializar Ray
    ray.init(ignore_reinit_error=True)
    
    # MediaPipe drawing utilities
    mp_hands = mp.solutions.hands
    mp_pose = mp.solutions.pose
    mp_draw = mp.solutions.drawing_utils
    
    try:
        # Crear agentes distribuidos
        print("[Ray] Inicializando agentes...")
        hand_agent = HandAgent.remote()
        pose_agent = PoseAgent.remote()
        object_agent = ObjectAgent.remote()
        print("[Ray] Agentes listos\n")
        
        # Abrir cámara
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: No se pudo abrir la cámara")
            return
        
        cv2.namedWindow('Agente de Deteccion', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Agente de Deteccion', 1280, 720)
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Procesar en paralelo con agentes
            hand_future = hand_agent.detect.remote(frame.copy())
            pose_future = pose_agent.detect.remote(frame.copy())
            
            # YOLO cada 3 frames para mejor rendimiento
            if frame_count % 3 == 0:
                obj_future = object_agent.detect.remote(frame.copy())
                objects = ray.get(obj_future)
            else:
                objects = []
            
            # Obtener resultados
            hand_landmarks_list, hands_data = ray.get(hand_future)
            pose_landmarks = ray.get(pose_future)
            
            # Dibujar TODO en el frame original
            # 1. Dibujar manos
            for hand_landmarks in hand_landmarks_list:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # 2. Dibujar pose
            if pose_landmarks:
                mp_draw.draw_landmarks(frame, pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # 3. Dibujar objetos
            for obj in objects:
                x1, y1, x2, y2 = obj['bbox']
                class_name = obj['class']
                confidence = obj['confidence']
                
                color = (0, 255, 0) if class_name == 'person' else (255, 165, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f'{class_name}: {confidence:.2f}', 
                           (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Verificar reglas de seguridad
            alerts = check_safety_rules(hands_data, pose_landmarks, objects)
            
            # Mostrar alertas en pantalla
            y_offset = 30
            for alert in alerts:
                cv2.putText(frame, alert, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                y_offset += 25
            
            # Título
            cv2.putText(frame, "Ray Agent: Puesto Agujereadora", (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Agente de Deteccion', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nProcesados {frame_count} frames")
    
    finally:
        ray.shutdown()
        print("[Ray] Sistema detenido")


if __name__ == "__main__":
    main()
