import os
import time
import json
import math
import threading
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import numpy as np
import av
from tenacity import retry, wait_exponential, stop_after_attempt
from ultralytics import YOLO

# Configuration
RTMP_URL = "rtmp://82.112.235.249:1935/input/1"
SAMPLE_FPS = 1  # analyze 1 frame per second
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
CONF_THRESH = float(os.getenv("YOLO_CONF", "0.35"))
IOU_THRESH = float(os.getenv("YOLO_IOU", "0.5"))
OUTPUT_JSONL = Path("../human_events.jsonl")

class PersonDetector:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL)
        self.name_to_id = {name: idx for idx, name in self.model.names.items()}
        self.person_id = self.name_to_id.get("person", 0)
        
        try:
            import torch
            self.device = 0 if torch.cuda.is_available() else "cpu"
        except Exception:
            self.device = "cpu"
        
        self.is_running = False
        self.detection_thread = None
        self.recent_detections = []
        self.alert_callbacks = []
        
        print(f"[PersonDetector] Initialized with device: {self.device}")
    
    def detect_persons(self, np_rgb: np.ndarray) -> Dict[str, Any]:
        """Run YOLO and return a dict with person_count and boxes for persons only."""
        try:
            res = self.model.predict(
                source=np_rgb,
                conf=CONF_THRESH,
                iou=IOU_THRESH,
                imgsz=640,
                device=self.device,
                verbose=False
            )[0]

            if res.boxes is None or len(res.boxes) == 0:
                return {"person_count": 0, "boxes": []}

            cls = res.boxes.cls.cpu().numpy().astype(int)
            conf = res.boxes.conf.cpu().numpy().tolist()
            xyxy = res.boxes.xyxy.cpu().numpy().tolist()

            boxes_person = []
            for c, b, p in zip(cls, xyxy, conf):
                if c == self.person_id:
                    boxes_person.append([float(b[0]), float(b[1]), float(b[2]), float(b[3]), float(p)])

            return {"person_count": len(boxes_person), "boxes": boxes_person}
        except Exception as e:
            print(f"[PersonDetector] Detection error: {e}")
            return {"person_count": 0, "boxes": []}

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10),
           stop=stop_after_attempt(10))
    def open_container(self, url: str) -> av.container.InputContainer:
        return av.open(url, timeout=5.0)

    def add_alert_callback(self, callback):
        """Add a callback function to be called when a person is detected"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback):
        """Remove a callback function"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    def _notify_callbacks(self, detection_data):
        """Notify all registered callbacks about a new detection"""
        for callback in self.alert_callbacks:
            try:
                callback(detection_data)
            except Exception as e:
                print(f"[PersonDetector] Callback error: {e}")

    def stream_and_analyze(self, rtmp_url: str):
        """Main detection loop"""
        print(f"[PersonDetector] Connecting to {rtmp_url}...")
        container = self.open_container(rtmp_url)

        if not container.streams.video:
            raise RuntimeError("No video stream found.")

        vstream = container.streams.video[0]
        vstream.thread_type = "AUTO"

        last_whole_sec = -1
        start_monotonic = time.monotonic()

        # Ensure output directory exists
        OUTPUT_JSONL.parent.mkdir(exist_ok=True)

        # Open JSONL file in append mode
        with open(OUTPUT_JSONL, "a", buffering=1) as fp:
            for frame in container.decode(video=0):
                if not self.is_running:
                    break

                # Derive timestamp in seconds
                if frame.pts is None or vstream.time_base is None:
                    t_sec = time.monotonic() - start_monotonic
                else:
                    t_sec = float(frame.pts * vstream.time_base)

                current_sec = int(math.floor(t_sec))
                if current_sec == last_whole_sec:
                    continue
                last_whole_sec = current_sec

                # Convert frame to RGB numpy
                np_rgb = frame.to_ndarray(format="rgb24")

                # Run YOLO person detection
                try:
                    det = self.detect_persons(np_rgb)
                except Exception as e:
                    print(f"[PersonDetector] YOLO inference failed: {e}")
                    continue

                # Log when at least one human is detected
                if det["person_count"] > 0:
                    event = {
                        "ts_stream_sec": current_sec,
                        "wallclock_iso": datetime.utcnow().isoformat() + "Z",
                        "person_count": det["person_count"],
                        "boxes_xyxy_conf": det["boxes"],
                    }
                    
                    # Write to JSONL file
                    fp.write(json.dumps(event) + "\n")
                    fp.flush()
                    
                    # Store in recent detections
                    self.recent_detections.append(event)
                    if len(self.recent_detections) > 100:  # Keep last 100 detections
                        self.recent_detections = self.recent_detections[-100:]
                    
                    # Notify callbacks
                    self._notify_callbacks(event)
                    
                    print(f"[PersonDetector] {json.dumps(event)}")

    def start_detection(self):
        """Start the person detection in a separate thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        print("[PersonDetector] Detection started")

    def stop_detection(self):
        """Stop the person detection"""
        self.is_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=5)
        print("[PersonDetector] Detection stopped")

    def _detection_loop(self):
        """Main detection loop with reconnection logic"""
        while self.is_running:
            try:
                self.stream_and_analyze(RTMP_URL)
            except KeyboardInterrupt:
                print("\n[PersonDetector] Stopping.")
                break
            except Exception as e:
                print(f"[PersonDetector] Stream error: {e}. Reconnecting in 3s...")
                time.sleep(3)

    def get_recent_detections(self, limit: int = 50) -> List[Dict]:
        """Get recent detections"""
        return self.recent_detections[-limit:] if self.recent_detections else []

# Global detector instance
detector = PersonDetector()
