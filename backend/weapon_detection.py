import os
import time
import json
import threading
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np
from ultralytics import YOLO

class WeaponDetector:
    """
    Dedicated weapon detection class for identifying firearms and knives.
    This is treated as a CRITICAL ALERT system.
    """
    
    def __init__(self, model_path: str = None):
        # Use environment variables for configuration
        self.model_path = model_path or os.getenv("WEAPON_MODEL_PATH", "models/weapon_detection.pt")
        self.model = None
        self.weapon_classes = {}
        self.conf_threshold = float(os.getenv("WEAPON_CONF_THRESHOLD", "0.7"))  # Higher confidence for weapons
        self.is_initialized = False
        
        # Critical alert callbacks
        self.critical_alert_callbacks = []
        
        # Weapon detection history for tracking
        self.weapon_detections = []
        self.last_weapon_alert = 0
        self.alert_cooldown = float(os.getenv("WEAPON_ALERT_COOLDOWN", "2.0"))  # Configurable cooldown
        
        try:
            self._initialize_model()
        except Exception as e:
            print(f"❌ Failed to initialize weapon detector: {e}")
    
    def _initialize_model(self):
        """Initialize the weapon detection model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Weapon detection model not found at {self.model_path}")
        
        print(f"🔫 Loading weapon detection model from {self.model_path}")
        self.model = YOLO(self.model_path)
        
        # Get model classes
        self.weapon_classes = self.model.names
        print(f"🎯 Weapon detection classes: {self.weapon_classes}")
        
        self.is_initialized = True
        print("✅ Weapon detector initialized successfully")
    
    def detect_weapons(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect weapons in a frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of weapon detections with format:
            {
                'class_name': str,
                'class_id': int,
                'confidence': float,
                'bbox': [x1, y1, x2, y2],
                'timestamp': str,
                'alert_level': 'CRITICAL'
            }
        """
        if not self.is_initialized or self.model is None:
            return []
        
        detections = []
        
        try:
            # Run weapon detection
            results = self.model(frame, conf=self.conf_threshold, verbose=False)
            
            current_time = datetime.now()
            
            for result in results:
                if result.boxes is None:
                    continue
                
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                    weapon_detection = {
                        'class_name': self.weapon_classes.get(class_id, f'weapon_{class_id}'),
                        'class_id': int(class_id),
                        'confidence': float(conf),
                        'bbox': [float(x) for x in box],
                        'timestamp': current_time.isoformat(),
                        'alert_level': 'CRITICAL',
                        'detection_type': 'weapon'
                    }
                    
                    detections.append(weapon_detection)
                    
                    # Trigger critical alert if cooldown has passed
                    current_timestamp = time.time()
                    if current_timestamp - self.last_weapon_alert > self.alert_cooldown:
                        self._trigger_critical_alert(weapon_detection)
                        self.last_weapon_alert = current_timestamp
            
            # Store detection history
            if detections:
                self.weapon_detections.extend(detections)
                # Keep only last 100 detections to prevent memory issues
                self.weapon_detections = self.weapon_detections[-100:]
                
        except Exception as e:
            print(f"❌ Error in weapon detection: {e}")
        
        return detections
    
    def _trigger_critical_alert(self, detection: Dict[str, Any]):
        """Trigger critical alert for weapon detection"""
        alert_data = {
            'alert_type': 'CRITICAL_WEAPON_DETECTED',
            'detection': detection,
            'timestamp': detection['timestamp'],
            'threat_level': 'HIGH',
            'requires_immediate_attention': True
        }
        
        print(f"🚨 CRITICAL ALERT: {detection['class_name']} detected with {detection['confidence']:.2f} confidence!")
        
        # Call all registered critical alert callbacks
        for callback in self.critical_alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                print(f"❌ Error in critical alert callback: {e}")
    
    def add_critical_alert_callback(self, callback):
        """Add callback for critical weapon alerts"""
        self.critical_alert_callbacks.append(callback)
    
    def get_recent_detections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent weapon detections"""
        return self.weapon_detections[-limit:] if self.weapon_detections else []
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get weapon detection statistics"""
        if not self.weapon_detections:
            return {
                'total_detections': 0,
                'unique_weapons': 0,
                'last_detection': None,
                'threat_level': 'NONE'
            }
        
        weapon_types = set(d['class_name'] for d in self.weapon_detections)
        
        return {
            'total_detections': len(self.weapon_detections),
            'unique_weapons': len(weapon_types),
            'weapon_types': list(weapon_types),
            'last_detection': self.weapon_detections[-1]['timestamp'],
            'threat_level': 'HIGH' if self.weapon_detections else 'NONE'
        }
    
    def reset_detection_history(self):
        """Reset weapon detection history"""
        self.weapon_detections = []
        print("🔄 Weapon detection history reset")

class CriticalAlertManager:
    """
    Manager for critical alerts including weapons detection
    """
    
    def __init__(self):
        self.critical_events = []
        self.alert_callbacks = []
        self.emergency_log_file = Path("critical_alerts.jsonl")
    
    def handle_critical_alert(self, alert_data: Dict[str, Any]):
        """Handle critical weapon detection alerts"""
        # Log to critical events
        self.critical_events.append(alert_data)
        
        # Log to emergency file
        try:
            with open(self.emergency_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert_data) + "\n")
        except Exception as e:
            print(f"❌ Failed to log critical alert: {e}")
        
        # Trigger all alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                print(f"❌ Error in alert callback: {e}")
        
        print(f"🚨 CRITICAL ALERT LOGGED: {alert_data['alert_type']}")
    
    def add_alert_callback(self, callback):
        """Add callback for critical alerts"""
        self.alert_callbacks.append(callback)
    
    def get_recent_critical_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent critical events"""
        return self.critical_events[-limit:] if self.critical_events else []
