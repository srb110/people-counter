"""
Main Server - Receives images from Raspberry Pi
Stores them, manages database, triggers GPU processing.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, BackgroundTasks
from datetime import datetime
from pathlib import Path
import logging
import shutil
import config
import database as db
from batch_processor import run_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MAIN - %(levelname)s - %(message)s'
)

# Initialize database on startup
db.init_database()

# Ensure folders exist
config.PENDING_DIR.mkdir(parents=True, exist_ok=True)
config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Main Server - Image Receiver")


def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@app.get("/health")
async def health_check():
    return {
        "status": "alive",
        "service": "main_server",
        "stats": db.get_stats()
    }


@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    timestamp: str = Form(...),
    device_id: str = Form("pi-01"),
    x_api_key: str = Header(None)
):
    """Receive image from Raspberry Pi"""
    verify_api_key(x_api_key)
    
    # Generate unique filename: deviceID_timestamp_originalname
    safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
    new_filename = f"{device_id}_{safe_timestamp}_{file.filename}"
    file_path = config.PENDING_DIR / new_filename
    
    try:
        # Save image
        with file_path.open('wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # Record in database
        image_id = db.insert_image(
            filename=new_filename,
            captured_at=timestamp,
            file_path=file_path
        )
        
        logging.info(f"Received: {new_filename} (id={image_id})")
        
        return {
            "status": "ok",
            "image_id": image_id,
            "filename": new_filename,
            "received_at": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process_batch")
async def trigger_batch_processing(
    background_tasks: BackgroundTasks,
    batch_size: int = None,
    x_api_key: str = Header(None)
):
    """Trigger batch processing - sends pending images to GPU server"""
    verify_api_key(x_api_key)
    
    # Run in background so request returns immediately
    background_tasks.add_task(run_batch, batch_size)
    
    return {
        "status": "batch_started",
        "message": "Batch processing started in background"
    }


@app.get("/stats")
async def get_statistics(x_api_key: str = Header(None)):
    """Get processing statistics"""
    verify_api_key(x_api_key)
    return db.get_stats()


@app.get("/export/csv")
async def export_csv(
    from_date: str = None,
    to_date: str = None,
    x_api_key: str = Header(None)
):
    """
    Export all processed results as CSV file.
    For use by ML team to train models on synchronized data.
    
    Optional query parameters:
    - from_date: ISO format like 2026-05-11T00:00:00
    - to_date: ISO format like 2026-05-12T00:00:00
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    verify_api_key(x_api_key)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Build query with optional date filtering
    query = """
        SELECT captured_at, people_count, filename, model_used, 
               processing_time_ms
        FROM images
        WHERE status = 'processed'
    """
    params = []
    
    if from_date:
        query += " AND captured_at >= ?"
        params.append(from_date)
    if to_date:
        query += " AND captured_at <= ?"
        params.append(to_date)
    
    query += " ORDER BY captured_at"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row - what ML team needs
    writer.writerow([
        "timestamp",
        "people_count",
        "filename",
        "model_used",
        "processing_time_ms"
    ])
    
    # Data rows
    for row in rows:
        writer.writerow([
            row['captured_at'],
            row['people_count'],
            row['filename'],
            row['model_used'],
            row['processing_time_ms']
        ])
    
    output.seek(0)
    
    # Return as downloadable file
    filename = f"people_counts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/results")
async def get_results(
    limit: int = 20,
    x_api_key: str = Header(None)
):
    """Get recent processed results"""
    verify_api_key(x_api_key)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT filename, captured_at, people_count, processed_at, processing_time_ms
        FROM images
        WHERE status = 'processed'
        ORDER BY processed_at DESC
        LIMIT ?
    """, (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"count": len(results), "results": results}


if __name__ == "__main__":
    import uvicorn
    logging.info(f"Starting Main Server on port {config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)