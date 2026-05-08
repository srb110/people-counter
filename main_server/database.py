"""
SQLite database for tracking images and their processing status.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import config


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_database():
    """Create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            captured_at TEXT NOT NULL,
            received_at TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            people_count INTEGER,
            model_used TEXT,
            processed_at TEXT,
            processing_time_ms INTEGER,
            error_message TEXT
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON images(status)
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {config.DATABASE_PATH}")


def insert_image(filename, captured_at, file_path):
    """Record a new image arrival"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO images (filename, captured_at, received_at, file_path, status)
        VALUES (?, ?, ?, ?, 'pending')
    """, (filename, captured_at, datetime.now().isoformat(), str(file_path)))
    
    image_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return image_id


def get_pending_images(limit=None):
    """Get images that haven't been processed yet"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM images WHERE status = 'pending' ORDER BY captured_at"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_image_result(image_id, people_count, model_used, processing_time_ms, new_path):
    """Update image with GPU processing result"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE images 
        SET status = 'processed',
            people_count = ?,
            model_used = ?,
            processed_at = ?,
            processing_time_ms = ?,
            file_path = ?
        WHERE id = ?
    """, (people_count, model_used, datetime.now().isoformat(), 
          processing_time_ms, str(new_path), image_id))
    
    conn.commit()
    conn.close()


def mark_image_failed(image_id, error_message):
    """Mark an image as failed processing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE images 
        SET status = 'failed', error_message = ?
        WHERE id = ?
    """, (error_message, image_id))
    
    conn.commit()
    conn.close()


def get_stats():
    """Get statistics about processing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM images 
        GROUP BY status
    """)
    
    stats = {row['status']: row['count'] for row in cursor.fetchall()}
    conn.close()
    return stats