"""
Batch processor - sends pending images to GPU server.
Can be triggered manually, via API endpoint, or via cron.
"""
import requests
import shutil
import logging
from pathlib import Path
from datetime import datetime
import database as db
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - BATCH - %(levelname)s - %(message)s'
)


def process_single_image(image_record):
    """Send one image to GPU server, update database with result"""
    image_id = image_record['id']
    filename = image_record['filename']
    file_path = Path(image_record['file_path'])
    captured_at = image_record['captured_at']
    
    if not file_path.exists():
        logging.error(f"File not found: {file_path}")
        db.mark_image_failed(image_id, "File missing")
        return False
    
    try:
        # Send to GPU server
        with file_path.open('rb') as f:
            response = requests.post(
                f"{config.GPU_SERVER_URL}/detect",
                files={'file': (filename, f, 'image/jpeg')},
                data={'timestamp': captured_at},
                headers={'x-api-key': config.GPU_SERVER_API_KEY},
                timeout=config.GPU_REQUEST_TIMEOUT
            )
        
        if response.status_code != 200:
            error = f"GPU returned {response.status_code}: {response.text}"
            logging.error(error)
            db.mark_image_failed(image_id, error)
            return False
        
        result = response.json()
        
        # Move image to processed folder
        new_path = config.PROCESSED_DIR / filename
        shutil.move(str(file_path), str(new_path))
        
        # Update database
        db.update_image_result(
            image_id=image_id,
            people_count=result['people_count'],
            model_used=result['model_used'],
            processing_time_ms=result['processing_time_ms'],
            new_path=new_path
        )
        
        logging.info(
            f" {filename} → {result['people_count']} people "
            f"({result['processing_time_ms']}ms)"
        )
        return True
        
    except requests.exceptions.RequestException as e:
        error = f"Network error: {e}"
        logging.error(error)
        db.mark_image_failed(image_id, error)
        return False
    except Exception as e:
        error = f"Unexpected error: {e}"
        logging.error(error)
        db.mark_image_failed(image_id, error)
        return False


def run_batch(batch_size=None):
    """Process a batch of pending images"""
    if batch_size is None:
        batch_size = config.BATCH_SIZE
    
    images = db.get_pending_images(limit=batch_size)
    
    if not images:
        logging.info("No pending images to process")
        return {"processed": 0, "failed": 0}
    
    logging.info(f"Starting batch: {len(images)} images")
    
    success_count = 0
    fail_count = 0
    
    for image in images:
        if process_single_image(image):
            success_count += 1
        else:
            fail_count += 1
    
    logging.info(f"Batch complete: {success_count} success, {fail_count} failed")
    return {"processed": success_count, "failed": fail_count}


if __name__ == "__main__":
    # Manual trigger - run this script directly
    print("Running batch processor manually...")
    result = run_batch()
    print(f"\nResult: {result}")
    print(f"Stats: {db.get_stats()}")
