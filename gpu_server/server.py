"""
GPU Server - Mock YOLO inference
Receives images from main server, returns people count.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from datetime import datetime
import random
import time
import logging
import config

print(config)
print(config.__file__)
print(dir(config))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GPU - %(levelname)s - %(message)s'
)

app = FastAPI(title="GPU Inference Server")


def verify_api_key(x_api_key: str = Header(None)):
    """Check if request has valid API key"""
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.get("/health")
async def health_check():
    """Heartbeat endpoint"""
    return {"status": "alive", "service": "gpu_server"}


@app.post("/detect")
async def detect_people(
    file: UploadFile = File(...),
    timestamp: str = Form(...),
    x_api_key: str = Header(None)
):
    """
    Receive image, run mock YOLO, return people count.
    Real implementation will replace random with actual YOLO inference.
    """
    # Authentication
    verify_api_key(x_api_key)
    
    # Read image (we don't actually process it in mock)
    image_bytes = await file.read()
    image_size_kb = len(image_bytes) / 1024
    
    # Simulate processing time
    start = time.time()
    time.sleep(config.PROCESSING_DELAY_MS / 1000)
    
    # Mock YOLO output - random count
    people_count = random.randint(config.MIN_PEOPLE, config.MAX_PEOPLE)
    
    processing_time_ms = int((time.time() - start) * 1000)
    
    logging.info(
        f"Processed image: {file.filename} "
        f"({image_size_kb:.1f}KB) → {people_count} people"
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