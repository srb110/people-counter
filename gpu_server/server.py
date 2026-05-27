"""
GPU Server - Real YOLO11 inference for people counting.
Receives images from main server, returns people count + bounding boxes.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from datetime import datetime
import logging
import time
import io
from PIL import Image
from ultralytics import YOLO
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GPU - %(levelname)s - %(message)s'
)

app = FastAPI(title="GPU Inference Server")

# Load models at startup (only once)
logging.info("Loading YOLO11n model...")
yolo_model = YOLO("yolo11n.pt")
logging.info(" YOLO11n loaded")

# Class 0 in COCO is "person"
PERSON_CLASS_ID = 0


def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.get("/health")
async def health_check():
    return {
        "status": "alive",
        "service": "gpu_server",
        "models_loaded": ["yolo11n"]
    }


@app.post("/detect")
async def detect_people(
    file: UploadFile = File(...),
    timestamp: str = Form(...),
    x_api_key: str = Header(None)
):
    """
    Receive image, run real YOLO11 inference, return people count + boxes.
    """
    verify_api_key(x_api_key)
    
    # Read image
    image_bytes = await file.read()
    image_size_kb = len(image_bytes) / 1024
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")
    
    # Run YOLO inference
    start = time.time()
    results = yolo_model(image, verbose=False)
    processing_time_ms = int((time.time() - start) * 1000)
    
    # Extract person detections only
    boxes = results[0].boxes
    person_detections = []
    
    if boxes is not None and len(boxes) > 0:
        for i in range(len(boxes)):
            class_id = int(boxes.cls[i].item())
            if class_id == PERSON_CLASS_ID:
                confidence = float(boxes.conf[i].item())
                # xyxy format: [x1, y1, x2, y2]
                xyxy = boxes.xyxy[i].tolist()
                person_detections.append({
                    "bbox": [round(c, 1) for c in xyxy],
                    "confidence": round(confidence, 3)
                })
    
    people_count = len(person_detections)
    
    logging.info(
        f"YOLO: {file.filename} ({image_size_kb:.1f}KB) "
        f"→ {people_count} people ({processing_time_ms}ms)"
    )
    
    return {
        "timestamp": timestamp,
        "filename": file.filename,
        "people_count": people_count,
        "model_used": "yolo11n",
        "processing_time_ms": processing_time_ms,
        "image_size_kb": round(image_size_kb, 2),
        "detections": person_detections
    }


if __name__ == "__main__":
    import uvicorn
    logging.info(f"Starting GPU server on port {config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
