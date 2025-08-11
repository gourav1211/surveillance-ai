import os
import json
import asyncio
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import uvicorn
import traceback

# Configuration
RTMP_URL = "rtmp://82.112.235.249:1935/input/1"
HLS_OUTPUT_DIR = Path("./hls_output")
HLS_PLAYLIST = HLS_OUTPUT_DIR / "stream.m3u8"
JSONL_FILE = Path("../human_events.jsonl")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_ffmpeg_stream()
    global recent_alerts
    recent_alerts = load_recent_alerts()
    yield
    # Shutdown
    stop_ffmpeg_stream()

app = FastAPI(title="Surveillance AI API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
ffmpeg_process: Optional[subprocess.Popen] = None
recent_alerts: List[Dict] = []

def ensure_hls_directory():
    """Ensure HLS output directory exists"""
    HLS_OUTPUT_DIR.mkdir(exist_ok=True)

def start_ffmpeg_stream():
    """Start FFmpeg process to convert RTMP to HLS"""
    global ffmpeg_process
    
    ensure_hls_directory()
    
    if ffmpeg_process and ffmpeg_process.poll() is None:
        return  # Already running
    
    # FFmpeg command to convert RTMP to HLS
    cmd = [
        "ffmpeg",
        "-i", RTMP_URL,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "veryfast",
        "-g", "30",
        "-sc_threshold", "0",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_delete_threshold", "1",
        "-hls_flags", "delete_segments+append_list",
        "-reconnect", "1",
        "-reconnect_at_eof", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-y",
        str(HLS_PLAYLIST)
    ]
    
    try:
        # Start FFmpeg with error handling
        ffmpeg_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Started FFmpeg process with PID: {ffmpeg_process.pid}")
        
        # Start a thread to monitor FFmpeg output
        def monitor_ffmpeg():
            while ffmpeg_process and ffmpeg_process.poll() is None:
                stderr_line = ffmpeg_process.stderr.readline()
                if stderr_line:
                    print(f"FFmpeg: {stderr_line.strip()}")
                    # Check for specific error patterns
                    if "Connection refused" in stderr_line or "No route to host" in stderr_line:
                        print("FFmpeg: RTMP connection failed - source may be offline")
                    elif "Invalid data found" in stderr_line:
                        print("FFmpeg: Invalid stream data - check RTMP source")
        
        monitor_thread = threading.Thread(target=monitor_ffmpeg, daemon=True)
        monitor_thread.start()
        
    except FileNotFoundError:
        print("FFmpeg not found in PATH. Please install FFmpeg.")
        ffmpeg_process = None
    except Exception as e:
        print(f"Failed to start FFmpeg: {e}")
        print(traceback.format_exc())
        ffmpeg_process = None

def stop_ffmpeg_stream():
    """Stop FFmpeg process"""
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process.wait()
        ffmpeg_process = None
        print("Stopped FFmpeg process")

def load_recent_alerts(limit: int = 50) -> List[Dict]:
    """Load recent alerts from JSONL file"""
    alerts = []
    if not JSONL_FILE.exists():
        return alerts
    
    try:
        with open(JSONL_FILE, 'r') as f:
            lines = f.readlines()
            # Get the last 'limit' lines
            for line in lines[-limit:]:
                try:
                    event = json.loads(line.strip())
                    # Convert to frontend format
                    alert = {
                        "id": hash(event.get("wallclock_iso", "")),
                        "timestamp": datetime.fromisoformat(event["wallclock_iso"].replace('Z', '+00:00')).timestamp() * 1000,
                        "title": f"Motion Detected - {event['person_count']} Person{'s' if event['person_count'] > 1 else ''}",
                        "reason": f"Human presence detected with {event['person_count']} individual{'s' if event['person_count'] > 1 else ''}",
                        "severity": "critical" if event['person_count'] > 2 else "high" if event['person_count'] > 1 else "medium",
                        "location": "Camera Feed",
                        "details": f"Detected {event['person_count']} person{'s' if event['person_count'] > 1 else ''} at {event['wallclock_iso']}",
                        "detections": {
                            "objects": ["person"] * event['person_count'],
                            "confidence": max([box[4] for box in event['boxes_xyxy_conf']] + [0.0]),
                            "boxes": event['boxes_xyxy_conf']
                        }
                    }
                    alerts.append(alert)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error loading alerts: {e}")
    
    return alerts

# Ensure HLS directory exists before mounting
ensure_hls_directory()

# Serve HLS files
ensure_hls_directory()
app.mount("/hls", StaticFiles(directory=str(HLS_OUTPUT_DIR)), name="hls")

@app.get("/api/stream")
async def get_stream_info():
    """Get stream information"""
    # Check if FFmpeg process is running
    ffmpeg_running = ffmpeg_process is not None and ffmpeg_process.poll() is None
    
    # Check if HLS playlist exists
    playlist_exists = HLS_PLAYLIST.exists()
    
    if not ffmpeg_running:
        # Try to restart FFmpeg if it's not running
        start_ffmpeg_stream()
        
    # If still no playlist after attempting restart, return error but with more info
    if not playlist_exists:
        return {
            "url": "",
            "hls": "",
            "status": "unavailable",
            "type": "hls",
            "error": "Stream not available - RTMP source may be offline",
            "ffmpeg_running": ffmpeg_running,
            "playlist_exists": playlist_exists
        }
    
    return {
        "url": "http://localhost:8000/hls/stream.m3u8",
        "hls": "http://localhost:8000/hls/stream.m3u8",
        "status": "active",
        "type": "hls",
        "ffmpeg_running": ffmpeg_running,
        "playlist_exists": playlist_exists
    }

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary"""
    global recent_alerts
    
    # Refresh alerts
    recent_alerts = load_recent_alerts()
    
    total_alerts = len(recent_alerts)
    critical_alerts = len([a for a in recent_alerts if a["severity"] == "critical"])
    high_alerts = len([a for a in recent_alerts if a["severity"] == "high"])
    
    # Generate trend data with proper timestamps
    current_time = datetime.now()
    trend = []
    for i in range(24):
        hour_time = current_time.replace(hour=i, minute=0, second=0, microsecond=0)
        trend.append({
            "time": int(hour_time.timestamp() * 1000),  # Convert to milliseconds
            "alerts": max(0, 10 - abs(i - 12))
        })
    
    return {
        "total": total_alerts,
        "critical": critical_alerts,
        "high": high_alerts,
        "blackout": 0,
        "trend": trend
    }

@app.get("/api/alerts")
async def get_alerts(limit: int = 20, offset: int = 0):
    """Get alerts with pagination"""
    global recent_alerts
    
    # Refresh alerts
    recent_alerts = load_recent_alerts(limit + offset + 10)
    
    # Sort by timestamp (newest first)
    sorted_alerts = sorted(recent_alerts, key=lambda x: x["timestamp"], reverse=True)
    
    # Apply pagination
    paginated_alerts = sorted_alerts[offset:offset + limit]
    
    return paginated_alerts

@app.get("/api/alerts/stream")
async def stream_alerts():
    """Server-Sent Events endpoint for real-time alerts"""
    async def event_generator():
        last_count = len(recent_alerts)
        
        while True:
            # Check for new alerts
            current_alerts = load_recent_alerts()
            
            if len(current_alerts) > last_count:
                # New alerts detected
                new_alerts = current_alerts[last_count:]
                for alert in new_alerts:
                    yield f"data: {json.dumps(alert)}\n\n"
                
                last_count = len(current_alerts)
            
            await asyncio.sleep(2)  # Check every 2 seconds
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ffmpeg_running": ffmpeg_process is not None and ffmpeg_process.poll() is None,
        "hls_available": HLS_PLAYLIST.exists(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
