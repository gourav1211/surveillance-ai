import os
import time
import json
import math
import threading
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np
import av
from tenacity import retry, wait_exponential, stop_after_attempt
from ultralytics import YOLO

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables only")

try:
    import mediapipe as mp  # type: ignore
except Exception:
    mp = None  # mediapipe is optional; enable if installed

# Import weapon detection modules
from weapon_detection import WeaponDetector, CriticalAlertManager

# Configuration - Load from environment variables
RTMP_URL = os.getenv("RTMP_URL", "rtmp://82.112.235.249:1935/input/1")
SAMPLE_FPS = 1  # analyze 1 frame per second
YOLO_MODEL = os.getenv("YOLO_MODEL", "models/yolov8n.pt")
CONF_THRESH = float(os.getenv("YOLO_CONF", "0.55"))
IOU_THRESH = float(os.getenv("YOLO_IOU", "0.5"))
OUTPUT_JSONL = Path(os.getenv("OUTPUT_JSONL", "../human_events.jsonl"))

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
        
        # Performance optimization: frame counter for staggered weapon detection
        self.frame_count = 0
        self.weapon_detection_interval = int(os.getenv("WEAPON_DETECTION_INTERVAL", "3"))  # Configurable interval

        # Simple IOU-based multi-object tracker for deduplication
        # Tracks: track_id -> {"bbox": [x1,y1,x2,y2], "last_seen_sec": int, "hits": int}
        self.tracks: Dict[int, Dict[str, Any]] = {}
        self.next_track_id: int = 1
        self.iou_match_threshold: float = 0.35
        # With 1 FPS sampling, keep tracks alive for a few seconds to bridge short gaps
        self.max_track_age_seconds: int = 5
        
        # MediaPipe face-based deduplication
        self.mediapipe_enabled: bool = mp is not None
        self.face_detector = None
        if self.mediapipe_enabled:
            try:
                self.face_detector = mp.solutions.face_detection.FaceDetection(
                    model_selection=0,  # close-range
                    min_detection_confidence=0.5,
                )
            except Exception:
                self.face_detector = None
                self.mediapipe_enabled = False

        # Face registry: face_id -> {"embedding": np.ndarray, "last_seen_sec": int}
        self.face_registry: Dict[int, Dict[str, Any]] = {}
        self.next_face_id: int = 1
        # Cosine distance threshold for considering two faces the same
        self.face_match_threshold: float = 0.20
        self.face_registry_ttl_seconds: int = 120
        # Mapping of track_id to assigned face_id (when visible)
        self.track_to_face: Dict[int, int] = {}
        
        # Initialize weapon detection
        self.weapon_detector = None
        self.critical_alert_manager = CriticalAlertManager()
        
        weapon_model_enabled = os.getenv("ENABLE_WEAPON_DETECTION", "true").lower() == "true"
        if weapon_model_enabled:
            try:
                self.weapon_detector = WeaponDetector()
                if self.weapon_detector.is_initialized:
                    # Connect weapon detector to critical alert manager
                    self.weapon_detector.add_critical_alert_callback(
                        self.critical_alert_manager.handle_critical_alert
                    )
                    print("✅ Weapon detection integrated successfully")
                    print(f"🎯 Weapon classes: {self.weapon_detector.weapon_classes}")
                    print(f"⚙️ Weapon detection interval: every {self.weapon_detection_interval} frames")
                else:
                    print("⚠️ Weapon detection failed to initialize - model not loaded")
                    self.weapon_detector = None
            except FileNotFoundError as e:
                print(f"⚠️ Weapon model file not found: {e}")
                print("   Continuing without weapon detection...")
                self.weapon_detector = None
            except Exception as e:
                print(f"⚠️ Could not initialize weapon detection: {e}")
                print("   Continuing without weapon detection...")
                self.weapon_detector = None
        else:
            print("ℹ️ Weapon detection disabled via configuration")
        
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

    @staticmethod
    def _compute_iou(box_a: List[float], box_b: List[float]) -> float:
        xA = max(box_a[0], box_b[0])
        yA = max(box_a[1], box_b[1])
        xB = min(box_a[2], box_b[2])
        yB = min(box_a[3], box_b[3])

        inter_w = max(0.0, xB - xA)
        inter_h = max(0.0, yB - yA)
        inter_area = inter_w * inter_h

        if inter_area <= 0.0:
            return 0.0

        box_a_area = max(0.0, (box_a[2] - box_a[0])) * max(0.0, (box_a[3] - box_a[1]))
        box_b_area = max(0.0, (box_b[2] - box_b[0])) * max(0.0, (box_b[3] - box_b[1]))
        union_area = box_a_area + box_b_area - inter_area
        if union_area <= 0.0:
            return 0.0
        return inter_area / union_area

    def _update_tracks(self, boxes_xyxy_conf: List[List[float]], current_sec: int) -> Tuple[List[List[float]], List[int]]:
        """
        Match incoming person detections to existing tracks using IoU and return
        boxes augmented with track IDs, plus the list of newly created track IDs.
        """
        # Prepare structures
        unmatched_detection_indices = set(range(len(boxes_xyxy_conf)))
        track_ids = list(self.tracks.keys())
        matches: List[Tuple[int, int, float]] = []  # (track_id, det_idx, iou)

        # Compute all IoUs and collect potential matches
        for track_id in track_ids:
            track_bbox = self.tracks[track_id]["bbox"]
            best_det = -1
            best_iou = 0.0
            for det_idx, det in enumerate(boxes_xyxy_conf):
                if det_idx not in unmatched_detection_indices:
                    continue
                iou = self._compute_iou(track_bbox, det[:4])
                if iou > best_iou:
                    best_iou = iou
                    best_det = det_idx
            if best_det != -1 and best_iou >= self.iou_match_threshold:
                matches.append((track_id, best_det, best_iou))

        # Resolve conflicts by IoU (highest first) ensuring unique assignments
        matches.sort(key=lambda m: m[2], reverse=True)
        assigned_tracks = set()
        assigned_detections = set()
        confirmed_matches: List[Tuple[int, int]] = []
        for track_id, det_idx, _ in matches:
            if track_id in assigned_tracks or det_idx in assigned_detections:
                continue
            assigned_tracks.add(track_id)
            assigned_detections.add(det_idx)
            unmatched_detection_indices.discard(det_idx)
            confirmed_matches.append((track_id, det_idx))

        # Update matched tracks
        for track_id, det_idx in confirmed_matches:
            det = boxes_xyxy_conf[det_idx]
            self.tracks[track_id]["bbox"] = det[:4]
            self.tracks[track_id]["last_seen_sec"] = current_sec
            self.tracks[track_id]["hits"] = self.tracks[track_id].get("hits", 0) + 1

        # Create new tracks for unmatched detections
        new_track_ids: List[int] = []
        for det_idx in list(unmatched_detection_indices):
            det = boxes_xyxy_conf[det_idx]
            new_id = self.next_track_id
            self.next_track_id += 1
            self.tracks[new_id] = {
                "bbox": det[:4],
                "last_seen_sec": current_sec,
                "hits": 1,
            }
            new_track_ids.append(new_id)
            confirmed_matches.append((new_id, det_idx))

        # Drop stale tracks
        stale_ids = [tid for tid, t in self.tracks.items() if (current_sec - t["last_seen_sec"]) > self.max_track_age_seconds]
        for tid in stale_ids:
            self.tracks.pop(tid, None)

        # Build output list: [x1,y1,x2,y2,conf,track_id]
        tracks_with_ids: List[List[float]] = []
        for track_id, det_idx in confirmed_matches:
            det = boxes_xyxy_conf[det_idx]
            tracks_with_ids.append([float(det[0]), float(det[1]), float(det[2]), float(det[3]), float(det[4]), int(track_id)])

        return tracks_with_ids, new_track_ids

    # -------------------- Face utilities --------------------
    def _detect_faces(self, np_rgb: np.ndarray) -> List[Dict[str, Any]]:
        if not self.face_detector:
            return []
        try:
            h, w, _ = np_rgb.shape
            results = self.face_detector.process(np_rgb)
            faces = []
            if results and results.detections:
                for det in results.detections:
                    loc = det.location_data
                    if not loc or not loc.relative_bounding_box:
                        continue
                    rbb = loc.relative_bounding_box
                    x1 = max(0.0, rbb.xmin) * w
                    y1 = max(0.0, rbb.ymin) * h
                    bw = max(0.0, rbb.width) * w
                    bh = max(0.0, rbb.height) * h
                    x2 = min(float(w), x1 + bw)
                    y2 = min(float(h), y1 + bh)

                    # Convert keypoints to absolute image coords
                    kps_abs: List[Tuple[float, float]] = []
                    for kp in loc.relative_keypoints or []:
                        kps_abs.append((kp.x * w, kp.y * h))

                    faces.append({
                        "bbox": [x1, y1, x2, y2],
                        "keypoints_abs": kps_abs,
                        "score": float(det.score[0]) if det.score else 0.0,
                    })
            return faces
        except Exception:
            return []

    @staticmethod
    def _cosine_distance(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
        if denom <= 1e-8:
            return 1.0
        similarity = float(np.dot(vec_a, vec_b) / denom)
        return 1.0 - similarity

    def _compute_face_descriptor(self, face: Dict[str, Any]) -> Optional[np.ndarray]:
        # Build a simple descriptor from 6 mediapipe keypoints normalized by face box size
        bbox = face.get("bbox")
        kps_abs: List[Tuple[float, float]] = face.get("keypoints_abs", [])
        if not bbox or len(kps_abs) < 4:
            return None
        x1, y1, x2, y2 = bbox
        bw = max(1.0, x2 - x1)
        bh = max(1.0, y2 - y1)

        # Normalize keypoints to face box
        kps = [((x - x1) / bw, (y - y1) / bh) for (x, y) in kps_abs[:6]]
        # Choose pairwise distances among first up to 6 points
        distances: List[float] = []
        for i in range(len(kps)):
            for j in range(i + 1, len(kps)):
                dx = kps[i][0] - kps[j][0]
                dy = kps[i][1] - kps[j][1]
                distances.append(math.sqrt(dx * dx + dy * dy))
        if not distances:
            return None
        desc = np.array(distances, dtype=np.float32)
        # L2 normalize descriptor
        n = np.linalg.norm(desc)
        if n > 1e-8:
            desc = desc / n
        return desc

    def _match_or_register_face(self, descriptor: np.ndarray, current_sec: int) -> Tuple[int, bool]:
        # Try to find nearest in registry
        best_id = -1
        best_dist = 1.0
        for face_id, info in list(self.face_registry.items()):
            # Evict stale
            if (current_sec - info.get("last_seen_sec", 0)) > self.face_registry_ttl_seconds:
                self.face_registry.pop(face_id, None)
                continue
            dist = self._cosine_distance(descriptor, info["embedding"])
            if dist < best_dist:
                best_dist = dist
                best_id = face_id
        if best_id != -1 and best_dist <= self.face_match_threshold:
            # Update last seen and slight embedding update (EMA)
            prev = self.face_registry[best_id]["embedding"]
            new_emb = 0.8 * prev + 0.2 * descriptor
            # renormalize
            n = np.linalg.norm(new_emb)
            if n > 1e-8:
                new_emb = new_emb / n
            self.face_registry[best_id]["embedding"] = new_emb
            self.face_registry[best_id]["last_seen_sec"] = current_sec
            return best_id, False
        # Register new
        new_id = self.next_face_id
        self.next_face_id += 1
        self.face_registry[new_id] = {
            "embedding": descriptor,
            "last_seen_sec": current_sec,
        }
        return new_id, True

    def _assign_faces_to_tracks(self, np_rgb: np.ndarray, tracks_with_ids: List[List[float]], current_sec: int) -> Tuple[Dict[int, int], List[int], int]:
        """
        Returns:
          - mapping of track_id -> face_id (only for tracks with a matched face)
          - list of newly created face_ids in this frame
          - active_face_count (unique faces among active tracks)
        """
        if not self.mediapipe_enabled or not self.face_detector or not tracks_with_ids:
            return {}, [], 0

        faces = self._detect_faces(np_rgb)
        if not faces:
            return {}, [], 0

        # For each face, compute descriptor once
        face_descriptors: List[Optional[np.ndarray]] = [self._compute_face_descriptor(f) for f in faces]

        # Match faces to person tracks by IoU with the upper region of the person box
        def iou(a, b):
            return self._compute_iou(a, b)

        track_to_face: Dict[int, int] = {}
        new_face_ids: List[int] = []

        for box in tracks_with_ids:
            x1, y1, x2, y2, conf, track_id = box
            # focus on upper 60% of the person box
            up_box = [x1, y1, x2, y1 + 0.6 * (y2 - y1)]
            # Find best face inside this region
            best_idx = -1
            best_iou = 0.0
            for idx, f in enumerate(faces):
                fiou = iou(up_box, f["bbox"])
                if fiou > best_iou:
                    best_iou = fiou
                    best_idx = idx
            if best_idx == -1 or best_iou < 0.05:
                continue
            desc = face_descriptors[best_idx]
            if desc is None:
                continue
            face_id, is_new = self._match_or_register_face(desc, current_sec)
            track_to_face[int(track_id)] = face_id
            if is_new:
                new_face_ids.append(face_id)

        # Persist mapping
        for tid, fid in track_to_face.items():
            self.track_to_face[tid] = fid

        active_face_ids = set(track_to_face.values())
        return track_to_face, new_face_ids, len(active_face_ids)

    def stream_and_analyze(self, rtmp_url: str):
        """Main detection loop"""
        print(f"[PersonDetector] Connecting to {rtmp_url}...")
        container = self.open_container(rtmp_url)

        if not container.streams.video:
            raise RuntimeError("No video stream found.")

        vstream = container.streams.video[0]
        vstream.thread_type = "AUTO"
        # Prefer keyframes to reduce decoder overhead when sampling
        try:
            # Skip decoding non-keyframes; good enough when sampling at low FPS
            vstream.codec_context.skip_frame = "NONKEY"
        except Exception:
            pass

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
                
                # Increment frame counter for performance optimization
                self.frame_count += 1

                # Run YOLO person detection
                try:
                    det = self.detect_persons(np_rgb)
                except Exception as e:
                    print(f"[PersonDetector] YOLO inference failed: {e}")
                    continue

                # Run weapon detection (CRITICAL ALERT SYSTEM) - Optimized every 3 frames
                weapon_detections = []
                if (self.weapon_detector and self.weapon_detector.is_initialized and 
                    self.frame_count % self.weapon_detection_interval == 0):
                    try:
                        weapon_detections = self.weapon_detector.detect_weapons(np_rgb)
                        if weapon_detections:
                            print(f"🚨 WEAPONS DETECTED: {len(weapon_detections)} weapon(s) found!")
                    except Exception as e:
                        print(f"❌ Weapon detection failed: {e}")

                # Update tracker and deduplicate using track IDs + face identities
                if det["person_count"] > 0:
                    tracks_with_ids, new_track_ids = self._update_tracks(det["boxes"], current_sec)

                    # Assign faces to tracks and dedupe across track breaks
                    track_to_face, new_face_ids, active_face_count = self._assign_faces_to_tracks(np_rgb, tracks_with_ids, current_sec)

                    # Determine if we should emit an event:
                    # Prefer face-based dedupe: emit only when at least one new face identity appears.
                    # If face not available, fall back to new tracks.
                    should_emit = (len(new_face_ids) > 0) or (len(new_face_ids) == 0 and len(track_to_face) == 0 and len(new_track_ids) > 0)
                    if should_emit:
                        # Boxes corresponding to either new faces or new tracks (fallback)
                        chosen_track_ids = set()
                        if len(new_face_ids) > 0:
                            for tid, fid in track_to_face.items():
                                if fid in set(new_face_ids):
                                    chosen_track_ids.add(tid)
                        else:
                            chosen_track_ids.update(new_track_ids)

                        chosen_boxes = [box for box in tracks_with_ids if int(box[5]) in chosen_track_ids]

                        event = {
                            "ts_stream_sec": current_sec,
                            "wallclock_iso": datetime.utcnow().isoformat() + "Z",
                            # Backward-compatible fields (person_count still indicates new arrivals in this event)
                            "person_count": len(new_face_ids) if len(new_face_ids) > 0 else len(chosen_boxes),
                            "boxes_xyxy_conf": [b[:5] for b in chosen_boxes],
                            # Tracking/face context
                            "active_track_count": len(self.tracks),
                            "tracks_xyxy_conf_id": tracks_with_ids,
                            "new_track_ids": new_track_ids,
                            "track_to_face_id": track_to_face,
                            "new_face_ids": new_face_ids,
                            "active_face_count": active_face_count,
                            # CRITICAL: Weapon detection data
                            "weapon_detections": weapon_detections,
                            "has_weapons": len(weapon_detections) > 0,
                            "threat_level": "CRITICAL" if weapon_detections else "NORMAL"
                        }

                        # Write event
                        fp.write(json.dumps(event) + "\n")
                        fp.flush()

                        # Store in recent detections
                        self.recent_detections.append(event)
                        if len(self.recent_detections) > 100:
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

    def get_weapon_detection_stats(self) -> Dict[str, Any]:
        """Get weapon detection statistics"""
        if self.weapon_detector:
            return self.weapon_detector.get_detection_stats()
        return {
            'total_detections': 0,
            'unique_weapons': 0,
            'last_detection': None,
            'threat_level': 'NONE'
        }

    def get_critical_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent critical alerts"""
        if self.critical_alert_manager:
            return self.critical_alert_manager.get_recent_critical_events(limit)
        return []

    def add_critical_alert_callback(self, callback):
        """Add callback for critical alerts"""
        if self.critical_alert_manager:
            self.critical_alert_manager.add_alert_callback(callback)

# Global detector instance
detector = PersonDetector()
