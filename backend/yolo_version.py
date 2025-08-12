import os, io, time, json, math, sys
from typing import Dict, Any
import numpy as np
import av  # PyAV (FFmpeg bindings)
from tenacity import retry, wait_exponential, stop_after_attempt
from ultralytics import YOLO

RTMP_URL = "rtmp://82.112.235.249:1935/input/1"
SAMPLE_FPS = 1  # analyze 1 frame per second
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")  # swap to yolov8s.pt if needed
CONF_THRESH = float(os.getenv("YOLO_CONF", "0.35"))
IOU_THRESH = float(os.getenv("YOLO_IOU", "0.5"))
OUTPUT_JSONL = os.getenv("OUTPUT_JSONL", "human_events.jsonl")

# ---------------- YOLO init ----------------
model = YOLO(YOLO_MODEL)
# Map class name -> id once (expects COCO classes)
NAME_TO_ID = {name: idx for idx, name in model.names.items()}
PERSON_ID = NAME_TO_ID.get("person", 0)  # fallback to 0 if missing

try:
    import torch
    DEVICE = 0 if torch.cuda.is_available() else "cpu"
except Exception:
    DEVICE = "cpu"

# ------------- Streaming helpers -------------
@retry(wait=wait_exponential(multiplier=1, min=1, max=10),
       stop=stop_after_attempt(10))
def open_container(url: str) -> av.container.InputContainer:
    return av.open(url, timeout=5.0)

def detect_persons(np_rgb: np.ndarray) -> Dict[str, Any]:
    """
    Run YOLO and return a dict with person_count and boxes for persons only.
    boxes format: [x1, y1, x2, y2, confidence]
    """
    res = model.predict(
        source=np_rgb,
        conf=CONF_THRESH,
        iou=IOU_THRESH,
        imgsz=640,
        device=DEVICE,
        verbose=False
    )[0]

    if res.boxes is None or len(res.boxes) == 0:
        return {"person_count": 0, "boxes": []}

    cls = res.boxes.cls.cpu().numpy().astype(int)  # class ids
    conf = res.boxes.conf.cpu().numpy().tolist()
    xyxy = res.boxes.xyxy.cpu().numpy().tolist()

    boxes_person = []
    for c, b, p in zip(cls, xyxy, conf):
        if c == PERSON_ID:
            boxes_person.append([float(b[0]), float(b[1]), float(b[2]), float(b[3]), float(p)])

    return {"person_count": len(boxes_person), "boxes": boxes_person}

def stream_and_analyze(rtmp_url: str):
    print(f"[info] Connecting to {rtmp_url} …", flush=True)
    container = open_container(rtmp_url)

    if not container.streams.video:
        raise RuntimeError("No video stream found.")

    vstream = container.streams.video[0]
    vstream.thread_type = "AUTO"

    last_whole_sec = -1
    start_monotonic = time.monotonic()

    # Open JSONL file in append mode
    with open(OUTPUT_JSONL, "a", buffering=1) as fp:
        for frame in container.decode(video=0):
            # Derive timestamp in seconds (from PTS if available)
            if frame.pts is None or vstream.time_base is None:
                t_sec = time.monotonic() - start_monotonic
            else:
                t_sec = float(frame.pts * vstream.time_base)

            current_sec = int(math.floor(t_sec))
            if current_sec == last_whole_sec:
                continue  # already processed this second
            last_whole_sec = current_sec

            # Downsample to desired FPS (currently 1 FPS)
            # (If you later set SAMPLE_FPS != 1, adapt selection logic.)
            # Convert frame to RGB numpy
            np_rgb = frame.to_ndarray(format="rgb24")  # H x W x 3

            # Run YOLO person detection
            try:
                det = detect_persons(np_rgb)
            except Exception as e:
                print(f"[warn] YOLO inference failed: {e}", file=sys.stderr)
                continue

            # Log ONLY when at least one human is detected
            if det["person_count"] > 0:
                event = {
                    "ts_stream_sec": current_sec,
                    "wallclock_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "person_count": det["person_count"],
                    "boxes_xyxy_conf": det["boxes"],  # [x1,y1,x2,y2,conf] per person
                }
                fp.write(json.dumps(event) + "\n")
                print(json.dumps(event), flush=True)

def main():
    while True:
        try:
            stream_and_analyze(RTMP_URL)
        except KeyboardInterrupt:
            print("\n[info] Stopping.")
            break
        except Exception as e:
            print(f"[warn] Stream error: {e}. Reconnecting in 3s…", file=sys.stderr)
            time.sleep(3)

if __name__ == "__main__":
    main()
