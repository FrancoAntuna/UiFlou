# UiFlou - Desafío Técnico Computer Vision

Soluciones a problemas de procesamiento de video, streaming RTSP y arquitectura multiagente.

## 📦 Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso

```bash
python launcher.py
```

El launcher permite ejecutar cada problema. Seleccionar video MP4 opcionalmente (sin video = webcam).

---

## Problema 1: Procesamiento de Video

**Objetivo:** Pose estimation + HAR + Tracking + Ángulos + Export S3

### Herramientas
| Componente | Tecnología |
|------------|------------|
| Pose Estimation | YOLOv8-Pose |
| HAR | Ventana temporal 9s + clasificación |
| Tracking | ByteTrack (integrado YOLO) |
| Ángulos | Cálculo geométrico keypoints |
| Export | JSON cada 1s + Video MP4 |
| Storage | AWS S3 (boto3) |

### Ejecución
```bash
cd "Problema 1"
python main.py video.mp4
```

---

## Problema 2: Streaming RTSP

**Objetivo:** Pose estimation + Object detection sobre stream RTSP

### Herramientas
| Componente | Tecnología |
|------------|------------|
| Object Detection | YOLOv8n + Tracking |
| Pose Estimation | YOLOv8-Pose + Tracking |
| Video Output | MP4 (H.264) |
| Data Output | JSON por frame |

### Estructura del Sistema
```
Problema 2/
├── main.py              # Entry point
├── processors/
│   ├── detector.py      # Object detection + tracking
│   ├── pose_estimator.py # Pose + tracking
│   ├── video_writer.py  # Export video
│   └── data_exporter.py # Export JSON
├── output/              # JSONs
└── video_outputs/       # Videos procesados
```

### Formato de Video
- **Codec:** H.264
- **Container:** MP4
- **Resolución:** Original del source

### Formato de Datos
```json
{
  "frame_id": 0,
  "detections": [{"class": "person", "conf": 0.95, "bbox": [...], "track_id": 1}],
  "poses": [{"keypoints": [...], "track_id": 1}]
}
```

### Ejecución
```bash
cd "Problema 2"
python main.py --source rtsp://... 
# o sin --source para webcam
```

---

## Problema 3: Streaming Multicámara

**Objetivo:** Sistema de streaming para múltiples cámaras RTSP (mín. 3)

### Herramientas
| Componente | Tecnología |
|------------|------------|
| Streaming | OpenCV + Threading |
| Config | YAML dinámico |
| API REST | FastAPI + Uvicorn |
| Display | Grid layout OpenCV |

### Estructura
```
Problema 3/
├── main.py           # Entry point
├── camera_manager.py # Gestión de cámaras
├── camera_stream.py  # Stream individual
├── api.py            # REST API
└── config.yaml       # Configuración
```

### Modificación de Parámetros en Runtime
**Solución propuesta:** REST API (FastAPI)
- `GET /cameras` - Listar cámaras activas
- `POST /cameras` - Agregar cámara
- `DELETE /cameras/{id}` - Remover cámara
- `PUT /cameras/{id}/params` - Modificar parámetros
- `POST /recording/start` - Iniciar grabación
- Hot-reload de `config.yaml` con tecla 'r'

### ¿Real-time o Near Real-time?
**Near Real-time.** Razones:
1. **Buffering OpenCV:** Latencia de ~50-200ms por decode
2. **Threading overhead:** Sincronización entre streams
3. **Network latency:** RTSP agrega ~100-500ms
4. **Display sync:** Grid rendering introduce delay

Para real-time estricto se requeriría: GStreamer, hardware decode (NVDEC), zero-copy buffers.

---

## Problema 4: Agentes

### ¿Qué agentes para analizar video de puesto de trabajo?

La decisión de qué agentes utilizar está directamente relacionada al puesto de trabajo que se está controlando. No existe una solución única; depende del contexto operativo.

**Enfoque general propuesto:**

**Fase 1 - Agentes Core:**
1. **PoseAgent** - Detecta poses y posturas ergonómicas, yolov8-pose es de los mas robustos.
2. **HandDetectionAgent** - Detección de manos para monitoreo de tareas manuales, por ejemplo MediaPipe.
3. **SafetyAgent** - Detección de EPP (casco, guantes, chaleco). Implementación: red neuronal preentrenada (ej. YOLOv8) con fine-tuning sobre dataset de EPP específico

**Fase 2 - Agentes de Análisis:**
4. **TimeTrackingAgent** - Mide tiempos de actividades y ciclos de trabajo
5. **AnomalyAgent** - Detecta comportamientos inusuales o desviaciones del proceso estándar
6. **ActionAgent** - Clasifica acciones específicas del puesto (sentado, de pie, levantando peso)

### Arquitectura Multiagente

```
┌─────────────────────────────────────────────────┐
│                  Orchestrator                    │
│         (coordina, prioriza, combina)           │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Pose   │  │ Action │  │ Safety │  │Anomaly │
│ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │
└────┬───┘  └────┬───┘  └────┬───┘  └────┬───┘
     │           │           │           │
     └───────────┴─────┬─────┴───────────┘
                       ▼
              ┌─────────────────┐
              │  Shared Memory  │
              │  (Redis/Queue)  │
              └─────────────────┘
```

**Interacción:**
- Orchestrator distribuye frames a agentes
- Agentes procesan en paralelo y publican resultados
- Shared Memory permite comunicación inter-agente
- Orchestrator fusiona resultados y genera alertas

### Tecnologías/Frameworks

| Uso | Tecnología |
|-----|------------|
| Orquestación | LangGraph, CrewAI |
| Mensajería | Redis Streams, RabbitMQ |
| CV Models | Ultralytics, MediaPipe |
| LLM (opcional) | GPT-4V, LLaVA |

## 📋 Dependencias Consolidadas

```txt
ultralytics>=8.0.0
opencv-python>=4.8.0
numpy>=1.24.0
boto3>=1.28.0
pyyaml>=6.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
```
