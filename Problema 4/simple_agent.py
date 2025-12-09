"""
Agente Simple de Detección para Puesto de Trabajo (Agujereadora)
=================================================================
Este agente básico demuestra cómo detectar:
- Manos del operador (MediaPipe Hands)
- Pose corporal (MediaPipe Pose)
- Objetos relevantes como herramientas (YOLO)

Uso: python simple_agent.py
"""

import cv2
import mediapipe as mp
from ultralytics import YOLO

# Inicializar MediaPipe
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

# Inicializar YOLO para detección de objetos
model = YOLO('yolov8n.pt')  # Modelo nano, rápido y ligero

# Clases relevantes para puesto de trabajo con agujereadora
# (YOLO detecta muchos objetos, filtramos los relevantes)
RELEVANT_CLASSES = ['person', 'scissors', 'knife', 'bottle', 'cup', 'cell phone']


def detect_hands(frame, hands_detector):
    """Detecta manos y retorna landmarks."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(rgb)
    
    hand_data = []
    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Dibujar landmarks de la mano
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Guardar info de la mano
            hand_data.append({
                'type': handedness.classification[0].label,  # Left/Right
                'confidence': handedness.classification[0].score,
                'landmarks': [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
            })
    
    return frame, hand_data


def detect_pose(frame, pose_detector):
    """Detecta pose corporal y retorna landmarks."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_detector.process(rgb)
    
    pose_data = None
    if results.pose_landmarks:
        # Dibujar el esqueleto
        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        pose_data = {
            'landmarks': [(lm.x, lm.y, lm.z, lm.visibility) 
                         for lm in results.pose_landmarks.landmark]
        }
    
    return frame, pose_data


def detect_objects(frame, yolo_model):
    """Detecta objetos relevantes usando YOLO."""
    results = yolo_model(frame, verbose=False)[0]
    
    objects = []
    for box in results.boxes:
        class_id = int(box.cls[0])
        class_name = results.names[class_id]
        confidence = float(box.conf[0])
        
        # Solo mostrar objetos relevantes con confianza > 50%
        if confidence > 0.5:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Dibujar bounding box
            color = (0, 255, 0) if class_name == 'person' else (255, 165, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f'{class_name}: {confidence:.2f}', 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            objects.append({
                'class': class_name,
                'confidence': confidence,
                'bbox': (x1, y1, x2, y2)
            })
    
    return frame, objects


def check_safety_rules(hands_data, pose_data, objects):
    """
    Verifica reglas de seguridad simples.
    En un agente real, aquí iría lógica más compleja.
    """
    alerts = []
    
    # Regla 1: Detectar si hay manos cerca del área de trabajo
    if hands_data:
        alerts.append(f"✋ {len(hands_data)} mano(s) detectada(s)")
    
    # Regla 2: Verificar postura del operador
    if pose_data:
        alerts.append("👤 Operador detectado en posición")
    else:
        alerts.append("⚠️ Operador no visible")
    
    # Regla 3: Objetos en el área
    if objects:
        obj_names = [o['class'] for o in objects]
        alerts.append(f"📦 Objetos: {', '.join(set(obj_names))}")
    
    return alerts


def main():
    """Función principal del agente."""
    print("=" * 50)
    print("AGENTE DE DETECCIÓN - PUESTO DE TRABAJO")
    print("=" * 50)
    print("Presiona 'q' para salir\n")
    
    # Abrir cámara (0 = webcam por defecto)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    # Inicializar detectores
    hands = mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7
    )
    pose = mp_pose.Pose(
        min_detection_confidence=0.7
    )
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Aplicar detecciones
        frame, hands_data = detect_hands(frame, hands)
        frame, pose_data = detect_pose(frame, pose)
        
        # YOLO cada 3 frames para mejor rendimiento
        objects = []
        if frame_count % 3 == 0:
            frame, objects = detect_objects(frame, model)
        
        # Verificar reglas de seguridad
        alerts = check_safety_rules(hands_data, pose_data, objects)
        
        # Mostrar alertas en pantalla
        y_offset = 30
        for alert in alerts:
            cv2.putText(frame, alert, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            y_offset += 25
        
        # Título
        cv2.putText(frame, "Agente: Puesto Agujereadora", (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostrar frame
        cv2.imshow('Agente de Deteccion', frame)
        
        # Salir con 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Limpiar
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    pose.close()
    print("\nAgente detenido.")


if __name__ == "__main__":
    main()
