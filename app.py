"""
YT to WAV microservice — VPS par chalta hai.
POST /api/wav  {"url": "<youtube link>"}  +  Authorization: Bearer <secret>
  -> {"status":"ok","download_url":".../dl/<token>","filename":"....wav","expires_in":600}
GET  /dl/<token>   -> WAV file download (token 10 minute tak valid)
GET  /health       -> {"status":"ok"}
"""
import os
import re
import sys
import uuid
import time
import shutil
import threading
import subprocess
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_file, abort


def _load_dotenv():
    """Aas paas .env file ho to us se settings uthayein (local package ke liye)."""
    p = Path(__file__).resolve().parent / ".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

SECRET = os.environ.get("YTW_SECRET", "")
BASE_URL = os.environ.get("YTW_BASE_URL", "").rstrip("/")
PORT = int(os.environ.get("PORT", "8765"))
WORKDIR = Path(os.environ.get("WORKDIR", "/tmp/yt-wav"))
MAX_DURATION = int(os.environ.get("MAX_DURATION", "1200"))  # seconds
LINK_TTL = 600  # download link valid for 10 minutes
MAX_JOBS = 2    # concurrent conversions

app = Flask(__name__)

YT_RE = re.compile(
    r"^https?://(www\.|m\.|music\.)?youtube\.com/watch\?.*v=[\w-]{11}"
    r"|^https?://youtu\.be/[\w-]{11}"
    r"|^https?://(www\.)?youtube\.com/shorts/[\w-]{11}"
)

links = {}          # token -> {"path": Path, "name": str, "exp": float}
links_lock = threading.Lock()
job_slots = threading.Semaphore(MAX_JOBS)

# yt-dlp ka full path nikal lein (venv ke andar bhi mile)
YTDLP = shutil.which("yt-dlp") or os.path.join(os.path.dirname(sys.executable), "yt-dlp")
# yt-dlp 2026+ ko YouTube extraction ke liye JS runtime chahiye; node use karein
YTDLP_BASE = [YTDLP, "--js-runtimes", "node"]
# sirf testing ke liye (proxy wala mahol): YTDLP_NO_CHECK_CERT=1
if os.environ.get("YTDLP_NO_CHECK_CERT") == "1":
    YTDLP_BASE.append("--no-check-certificate")


def _ffmpeg_dir():
    """imageio-ffmpeg ka bundled ffmpeg (Windows/Mac par sab se aasan rasta)."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return os.path.dirname(exe)
    except Exception:
        pass
    return None


_FFMPEG_DIR = _ffmpeg_dir()
if _FFMPEG_DIR:
    YTDLP_BASE += ["--ffmpeg-location", _FFMPEG_DIR]


def check_auth():
    if not SECRET:
        return False
    return request.headers.get("Authorization", "") == f"Bearer {SECRET}"


def safe_title(title, fallback):
    title = re.sub(r"[^\w\-. ]", "_", (title or "").strip())[:80].strip()
    return title or fallback


def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    return m.group(1) if m else uuid.uuid4().hex[:11]


def cleanup_loop():
    while True:
        time.sleep(60)
        now = time.time()
        with links_lock:
            dead = [t for t, v in links.items() if v["exp"] < now]
            for t in dead:
                try:
                    shutil.rmtree(links[t]["path"].parent, ignore_errors=True)
                except Exception:
                    pass
                del links[t]


@app.post("/api/wav")
def make_wav():
    if not check_auth():
        return jsonify(status="error", message="unauthorized"), 401

    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url or not YT_RE.match(url):
        return jsonify(status="error", message="invalid youtube url"), 400

    if not job_slots.acquire(blocking=False):
        return jsonify(status="error", message="server busy, try again in a minute"), 429

    vid = video_id(url)
    jobdir = WORKDIR / uuid.uuid4().hex[:12]
    jobdir.mkdir(parents=True, exist_ok=True)
    try:
        # 1) title + duration (pehle check, phir download)
        try:
            tr = subprocess.run(
                YTDLP_BASE + ["--no-download", "--no-playlist",
                              "--print", "%(title)s\t%(duration)s", url],
                capture_output=True, text=True, timeout=25,
            )
            title, dur = "", 0
            if tr.returncode == 0 and tr.stdout.strip():
                t, _, d = tr.stdout.strip().rpartition("\t")
                title = t
                try:
                    dur = int(float(d))
                except ValueError:
                    dur = 0
            if dur > MAX_DURATION:
                return jsonify(status="error",
                               message=f"video too long (max {MAX_DURATION // 60} min)"), 400
        except Exception:
            title = ""
        name = safe_title(title, vid) + ".wav"

        # 2) download best audio + convert to wav
        out = jobdir / "audio.%(ext)s"
        cmd = YTDLP_BASE + [
            "--no-playlist",
            "-x", "--audio-format", "wav", "--audio-quality", "0",
            "-o", str(out), url,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        wavs = list(jobdir.glob("*.wav"))
        if r.returncode != 0 or not wavs:
            detail = (r.stderr or "")[-400:]
            return jsonify(status="error", message="download/convert failed", detail=detail), 422

        wav_path = jobdir / "audio.wav"
        wavs[0].rename(wav_path)

        token = uuid.uuid4().hex
        with links_lock:
            links[token] = {"path": wav_path, "name": name, "exp": time.time() + LINK_TTL}

        if not BASE_URL:
            return jsonify(status="error", message="server misconfigured"), 500
        return jsonify(
            status="ok",
            download_url=f"{BASE_URL}/dl/{token}",
            filename=name,
            expires_in=LINK_TTL,
        )
    except subprocess.TimeoutExpired:
        return jsonify(status="error", message="took too long, try a shorter video"), 504
    except Exception:
        traceback.print_exc()
        return jsonify(status="error", message="server error"), 500
    finally:
        job_slots.release()


@app.get("/dl/<token>")
def download(token):
    with links_lock:
        info = links.get(token)
        if not info or info["exp"] < time.time() or not info["path"].exists():
            if token in links:
                del links[token]
            abort(404)
        path, name = info["path"], info["name"]
    return send_file(path, as_attachment=True, download_name=name, mimetype="audio/wav")


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    WORKDIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=cleanup_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
