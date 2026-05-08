# People Counter Project

IoT system for counting people in indoor spaces.

## Architecture
- Raspberry Pi: captures images via camera, uploads via HTTP
- Main Server: receives, stores, manages batch processing
- GPU Server: runs YOLO/DETR inference (mock for now)
