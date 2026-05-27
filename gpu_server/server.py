"""
GPU Server - Mock inference for testing and demo.
Returns random people count until real YOLO is deployed.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from datetime import datetime
import logging
import time
import random
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GPU - %(levelname)s - %(message)s'
)

app = FastAPI(title="GPU Inference Server")

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/health")
async def health_check():
    return {
        "status": "alive",
        "service": "gpu_server",
        "mode": "mock"
    }

@app.post("/detect")
async def detect_people(
    file: UploadFile = File(...),
    timestamp: str = Form(...),
    x_api_key: str = Header(None)
):
    """
    Mock detection — returns random people count.
    Real YOLO11 will replace this when deployed on IRCICA GPU server.
    """
    verify_api_key(x_api_key)

    # Read image (not actually processed in mock)
    image_bytes = await file.read()
    image_size_kb = len(image_bytes) / 1024

    # Simulate processing time
    start = time.time()
    time.sleep(0.1)  # 100ms fake processing

    # Mock result — random count between 0 and 10
    people_count = random.randint(0, 10)
    processing_time_ms = int((time.time() - start) * 1000)

    logging.info(
        f"MOCK: {file.filename} ({image_size_kb:.1f}KB) "
        f"→ {people_count} people ({processing_time_ms}ms)"
    )

    return {
        "timestamp": timestamp,
        "filename": file.filename,
        "people_count": people_count,
        "model_used": "yolo_mock_v1",
        "processing_time_ms": processing_time_ms,
        "image_size_kb": round(image_size_kb, 2)
    }

if __name__ == "__main__":
    import uvicorn
    logging.info(f"Starting GPU server on port {config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
