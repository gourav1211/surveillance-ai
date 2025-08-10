import os, io, time, json, base64, math, sys
from typing import Dict, Any, Optional
import av  # PyAV (FFmpeg bindings)
from PIL import Image
from tenacity import retry, wait_exponential, stop_after_attempt

RTMP_URL = "rtmp://82.112.235.249:1935/input/1"
SAMPLE_FPS = 1  # 1 frame per second
PROVIDER = "openai"  # or "stub" to test without calling a model

# --------- VLM integration (swap this block for your provider) ----------
def analyze_with_vlm(image_bytes: bytes) -> Dict[str, Any]:
    """
    Return a JSON-like dict. Keep this provider-agnostic signature.
    Example output:
    {
      "threats": [{"label":"weapon","confidence":0.78}],
      "overall_risk": 0.62,
      "explanation": "A person appears to hold a handgun."
    }
    """
    if PROVIDER == "stub":
        # Always-safe stub for testing pipeline speed without API calls
        return {"threats": [], "overall_risk": 0.0, "explanation": "Stub"}
    elif PROVIDER == "openai":
        # OpenAI: GPT-4o/4o-mini vision via Chat Completions
        # Requires: pip install openai  and OPENAI_API_KEY env var set
        from openai import OpenAI
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "You are a security vision assistant. Analyze the image for potential threats. "
            "Return STRICT JSON with keys: threats (array of {label, confidence 0-1}), "
            "overall_risk (0-1), explanation (short string). "
            "Threat label examples: weapon, fire/smoke, explosion, fight/assault, intrusion, hazardous_object. "
            "If none, threats=[], overall_risk=0.0."
        )
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }]
        )
        text = resp.choices[0].message.content

        # Be defensive: pull JSON from the reply
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON block if model added prose
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except Exception:
                    pass
            return {"threats": [], "overall_risk": 0.0,
                    "explanation": f"Non-JSON response: {text[:200]}"}
    else:
        raise RuntimeError(f"Unknown PROVIDER={PROVIDER}")

# ------------- Streaming & frame sampling (1 fps) -----------------------
def jpeg_bytes_from_frame(frame: av.VideoFrame, quality: int = 85) -> bytes:
    pil = frame.to_image()  # PIL.Image
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()

@retry(wait=wait_exponential(multiplier=1, min=1, max=10),
       stop=stop_after_attempt(10))
def open_container(url: str) -> av.container.InputContainer:
    # For RTMP, FFmpeg will auto-detect FLV demuxer. These options help reconnect.
    # Not all builds surface every reconnect flag through PyAV; retry wrapper handles drops.
    return av.open(url, timeout=5.0)

def stream_and_analyze(rtmp_url: str):
    print(f"[info] Connecting to {rtmp_url} …", flush=True)
    container = open_container(rtmp_url)

    if not container.streams.video:
        raise RuntimeError("No video stream found.")

    vstream = container.streams.video[0]
    vstream.thread_type = "AUTO"

    last_whole_sec = -1
    start_monotonic = time.monotonic()
    frames_seen = 0
    processed = 0

    for frame in container.decode(video=0):
        frames_seen += 1
        # Use PTS to derive timestamp (seconds from stream start)
        if frame.pts is None or vstream.time_base is None:
            # Fallback to monotonic if timestamps unavailable
            t_sec = time.monotonic() - start_monotonic
        else:
            t_sec = float(frame.pts * vstream.time_base)

        current_sec = int(math.floor(t_sec))
        if current_sec == last_whole_sec:
            continue  # already processed this second
        last_whole_sec = current_sec

        # Downsample to target FPS (e.g., every 1 sec)
        # If you want 2 FPS, change the condition to (current_sec % 0.5 == 0) + adapt logic
        if SAMPLE_FPS == 1:
            pass
        else:
            # For general case, only take frames when second boundary aligns with desired rate
            if (current_sec * SAMPLE_FPS) % SAMPLE_FPS != 0:
                continue

        # Convert to JPEG bytes
        img_bytes = jpeg_bytes_from_frame(frame, quality=85)

        # Analyze via VLM
        try:
            result = analyze_with_vlm(img_bytes)
        except Exception as e:
            print(f"[warn] VLM call failed: {e}", file=sys.stderr)
            continue

        processed += 1
        # Minimal console log; adapt to your logging/metrics sink
        print(json.dumps({
            "ts_sec": current_sec,
            "result": result
        }, ensure_ascii=False))

def main():
    while True:
        try:
            stream_and_analyze(RTMP_URL)
        except KeyboardInterrupt:
            print("\n[info] Stopping.")
            break
        except Exception as e:
            # Auto-reconnect on drops
            print(f"[warn] Stream error: {e}. Reconnecting in 3s…", file=sys.stderr)
            time.sleep(3)

if __name__ == "__main__":
    main()
