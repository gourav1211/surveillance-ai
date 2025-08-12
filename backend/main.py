import os
import time
import json
import asyncio
import subprocess
import threading
import queue
import signal
import sys
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

# Import person detection
from person_detection import detector, YOLO_MODEL, CONF_THRESH

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
    
    # Start person detection
    detector.start_detection()
    
    yield
    # Shutdown
    detector.stop_detection()
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
    
    # FFmpeg command to convert RTMP to HLS with minimal CPU overhead
    # Use stream copy for video to avoid re-encoding contention with detection
    cmd = [
        "ffmpeg",
        "-fflags", "+genpts",
        "-i", RTMP_URL,
        "-copyts",
        "-vsync", "1",
        "-c:v", "copy",
        "-c:a", "aac",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "6",
        "-hls_delete_threshold", "1",
        # independent_segments ensures each segment starts with a keyframe for better live playback
        "-hls_flags", "delete_segments+append_list+independent_segments",
        "-reconnect", "1",
        "-reconnect_at_eof", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-y",
        str(HLS_PLAYLIST)
    ]
    
    try:
        # Start FFmpeg with error handling and unbuffered output
        # Handle cross-platform process group creation
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "bufsize": 0,  # Unbuffered
        }
        
        # Add process group creation for Unix systems only
        if hasattr(os, 'setsid'):
            kwargs["preexec_fn"] = os.setsid
        elif os.name == 'nt':  # Windows
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        
        ffmpeg_process = subprocess.Popen(cmd, **kwargs)
        print(f"Started FFmpeg process with PID: {ffmpeg_process.pid}")
        
        # Start a thread to monitor FFmpeg output
        def monitor_ffmpeg():
            while ffmpeg_process and ffmpeg_process.poll() is None:
                try:
                    stderr_line = ffmpeg_process.stderr.readline()
                    if stderr_line:
                        print(f"FFmpeg: {stderr_line.strip()}")
                        # Check for specific error patterns
                        if "Connection refused" in stderr_line or "No route to host" in stderr_line:
                            print("FFmpeg: RTMP connection failed - source may be offline")
                        elif "Invalid data found" in stderr_line:
                            print("FFmpeg: Invalid stream data - check RTMP source")
                except Exception as e:
                    print(f"FFmpeg monitor error: {e}")
                    break
        
        monitor_thread = threading.Thread(target=monitor_ffmpeg, daemon=True)
        monitor_thread.start()
        
        # Start a thread to monitor and restart FFmpeg if it crashes
        def monitor_and_restart():
            global ffmpeg_process
            while True:
                if ffmpeg_process and ffmpeg_process.poll() is not None:
                    print(f"FFmpeg process exited with code {ffmpeg_process.returncode}")
                    if ffmpeg_process.returncode != 0:
                        print("FFmpeg crashed, restarting in 3 seconds...")
                        time.sleep(3)
                        # Clear the process reference before restarting
                        ffmpeg_process = None
                        start_ffmpeg_stream()
                    break
                time.sleep(1)
        
        restart_thread = threading.Thread(target=monitor_and_restart, daemon=True)
        restart_thread.start()
        
    except FileNotFoundError:
        print("FFmpeg not found in PATH. Please install FFmpeg.")
        ffmpeg_process = None
    except Exception as e:
        print(f"Failed to start FFmpeg: {e}")
        print(traceback.format_exc())
        ffmpeg_process = None

def stop_ffmpeg_stream():
    """Stop FFmpeg process gracefully"""
    global ffmpeg_process
    if ffmpeg_process:
        try:
            # Try graceful termination first
            ffmpeg_process.terminate()
            
            # Wait for graceful shutdown (5 seconds)
            try:
                ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                print("FFmpeg graceful shutdown failed, forcing termination...")
                ffmpeg_process.kill()
                ffmpeg_process.wait()
            
            ffmpeg_process = None
            print("Stopped FFmpeg process")
        except Exception as e:
            print(f"Error stopping FFmpeg process: {e}")
            ffmpeg_process = None

def load_recent_alerts(limit: int = 50) -> List[Dict]:
    """Load recent alerts from JSONL file and detector memory"""
    alerts = []
    
    # First, try to get alerts from detector's recent detections
    try:
        recent_detections = detector.get_recent_detections(limit)
        for event in recent_detections:
            # Prefer face counts when available
            active_face_count = int(event.get("active_face_count", 0))
            active_track_count = int(event.get("active_track_count", event.get("person_count", 0)))
            active_count = active_face_count if active_face_count > 0 else active_track_count
            new_count = int(event.get("new_face_ids", []) and len(event.get("new_face_ids", [])) or event.get("person_count", 0))
            active_boxes_src = event.get("tracks_xyxy_conf_id") or []
            active_boxes = [[b[0], b[1], b[2], b[3], b[4]] for b in active_boxes_src] if active_boxes_src else event.get("boxes_xyxy_conf", [])
            alert = {
                "id": hash(event.get("wallclock_iso", "")),
                "timestamp": datetime.fromisoformat(event["wallclock_iso"].replace('Z', '+00:00')).timestamp() * 1000,
                "title": f"Motion Detected - {active_count} Active Person{'s' if active_count != 1 else ''}",
                "reason": f"{new_count} new individual{'s' if new_count != 1 else ''} detected; {active_count} active in view",
                "severity": "critical" if active_count > 2 else "high" if active_count > 1 else "medium",
                "location": "Camera Feed",
                "details": f"New: {new_count}, Active: {active_count} at {event['wallclock_iso']}",
                "person_count": active_count,
                "new_person_count": new_count,
                "detections": {
                    "objects": ["person"] * active_count,
                    "confidence": max([box[4] for box in active_boxes] + [0.0]),
                    "boxes": active_boxes,
                }
            }
            alerts.append(alert)
    except Exception as e:
        print(f"Error loading detector alerts: {e}")
    
    # If no detector alerts, fall back to JSONL file
    if not alerts and JSONL_FILE.exists():
        try:
            with open(JSONL_FILE, 'r') as f:
                lines = f.readlines()
                # Get the last 'limit' lines
                for line in lines[-limit:]:
                    try:
                        event = json.loads(line.strip())
                        # Convert to frontend format
                        active_face_count = int(event.get("active_face_count", 0))
                        active_track_count = int(event.get("active_track_count", event.get("person_count", 0)))
                        active_count = active_face_count if active_face_count > 0 else active_track_count
                        new_count = int(event.get("new_face_ids", []) and len(event.get("new_face_ids", [])) or event.get("person_count", 0))
                        active_boxes_src = event.get("tracks_xyxy_conf_id") or []
                        active_boxes = [[b[0], b[1], b[2], b[3], b[4]] for b in active_boxes_src] if active_boxes_src else event.get("boxes_xyxy_conf", [])
                        alert = {
                            "id": hash(event.get("wallclock_iso", "")),
                            "timestamp": datetime.fromisoformat(event["wallclock_iso"].replace('Z', '+00:00')).timestamp() * 1000,
                            "title": f"Motion Detected - {active_count} Active Person{'s' if active_count != 1 else ''}",
                            "reason": f"{new_count} new individual{'s' if new_count != 1 else ''} detected; {active_count} active in view",
                            "severity": "critical" if active_count > 2 else "high" if active_count > 1 else "medium",
                            "location": "Camera Feed",
                            "details": f"New: {new_count}, Active: {active_count} at {event['wallclock_iso']}",
                            "person_count": active_count,
                            "new_person_count": new_count,
                            "detections": {
                                "objects": ["person"] * active_count,
                                "confidence": max([box[4] for box in active_boxes] + [0.0]),
                                "boxes": active_boxes,
                            }
                        }
                        alerts.append(alert)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error loading JSONL alerts: {e}")
    
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
        # Thread-safe queue to store new alerts
        alert_queue = queue.Queue()
        
        def on_detection(detection_data):
            """Callback for new detections"""
            try:
                active_count = int(detection_data.get("active_track_count", detection_data.get("person_count", 0)))
                new_count = int(detection_data.get("person_count", 0))
                active_boxes_src = detection_data.get("tracks_xyxy_conf_id") or []
                # Normalize to [x1,y1,x2,y2,conf]
                active_boxes = [[b[0], b[1], b[2], b[3], b[4]] for b in active_boxes_src] if active_boxes_src else detection_data.get("boxes_xyxy_conf", [])

                alert = {
                    "id": hash(detection_data.get("wallclock_iso", "")),
                    "timestamp": datetime.fromisoformat(detection_data["wallclock_iso"].replace('Z', '+00:00')).timestamp() * 1000,
                    "title": f"Motion Detected - {active_count} Active Person{'s' if active_count != 1 else ''}",
                    "reason": f"{new_count} new individual{'s' if new_count != 1 else ''} detected; {active_count} active in view",
                    "severity": "critical" if active_count > 2 else "high" if active_count > 1 else "medium",
                    "location": "Camera Feed",
                    "details": f"New: {new_count}, Active: {active_count} at {detection_data['wallclock_iso']}",
                    "person_count": active_count,
                    "new_person_count": new_count,
                    "detections": {
                        "objects": ["person"] * active_count,
                        "confidence": max([box[4] for box in active_boxes] + [0.0]),
                        "boxes": active_boxes,
                    }
                }
                # Put alert in thread-safe queue
                alert_queue.put(alert)
            except Exception as e:
                print(f"Error processing detection callback: {e}")
        
        # Register callback with detector
        detector.add_alert_callback(on_detection)
        
        try:
            while True:
                try:
                    # Wait for new alert with timeout
                    alert = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: alert_queue.get(timeout=30.0)
                    )
                    yield f"data: {json.dumps(alert)}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()})}\n\n"
        finally:
            # Clean up callback
            detector.remove_alert_callback(on_detection)
    
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
        "detection_running": detector.is_running,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/detection/status")
async def get_detection_status():
    """Get person detection status"""
    return {
        "is_running": detector.is_running,
        "device": detector.device,
        "model": YOLO_MODEL,
        "confidence_threshold": CONF_THRESH,
        "recent_detections_count": len(detector.recent_detections),
        "last_detection": detector.recent_detections[-1] if detector.recent_detections else None
    }

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    detector.stop_detection()
    stop_ffmpeg_stream()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
