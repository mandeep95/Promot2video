"""
Prompt2Video server (stdlib only — runs anywhere Python 3 runs).

  GET  /                 the website
  POST /api/script       {mode: demo|groq|paste, prompt, text, api_key,
                          brand} -> script JSON
  POST /api/render       {script} -> {job_id}
  GET  /api/job/<id>     {status, stage, done, total, video, error, meta}
  GET  /outputs/<id>.mp4 the rendered video

The user's Groq key is used per-request only and never stored.
"""

import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))
import generators  # noqa: E402
import renderer  # noqa: E402

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)
JOBS = {}
LOCK = threading.Lock()


def run_job(job_id, script, opts=None):
    job = JOBS[job_id]
    workdir = os.path.join(OUT, f"job-{job_id}")
    out_mp4 = os.path.join(OUT, f"{job_id}.mp4")

    def progress(stage, done, total):
        with LOCK:
            job.update(stage=stage, done=done, total=total)

    try:
        meta = renderer.render(script, out_mp4, workdir, progress, opts)
        # cover image from an early frame + history record
        cover = os.path.join(OUT, f"{job_id}.jpg")
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-ss", "1.2", "-i", out_mp4,
                        "-frames:v", "1", "-q:v", "3", cover],
                       capture_output=True)
        import time
        record = {"id": job_id, "title": script.get("title", "Untitled"),
                  "duration": meta["duration"], "scenes": meta["scenes"],
                  "created": int(time.time()),
                  "video": f"/outputs/{job_id}.mp4",
                  "cover": f"/outputs/{job_id}.jpg"}
        json.dump(record, open(os.path.join(OUT, f"{job_id}.json"), "w"))
        with LOCK:
            job.update(status="done", video=record["video"],
                       cover=record["cover"], meta=meta)
    except Exception as e:  # keep the error readable for the UI
        with LOCK:
            job.update(status="error", error=str(e)[:400])
    finally:
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            path = os.path.join(HERE, "web", "index.html")
            data = open(path, "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/api/job/"):
            job_id = self.path.split("/")[-1]
            job = JOBS.get(job_id)
            if not job:
                return self._json(404, {"error": "job not found"})
            self._json(200, {k: job.get(k) for k in
                             ("status", "stage", "done", "total", "video",
                              "cover", "error", "meta")})
        elif self.path == "/api/history":
            recs = []
            for name in os.listdir(OUT):
                if name.endswith(".json"):
                    try:
                        recs.append(json.load(
                            open(os.path.join(OUT, name))))
                    except Exception:
                        pass
            recs.sort(key=lambda r: r.get("created", 0), reverse=True)
            self._json(200, {"items": recs[:20]})
        elif self.path.startswith("/outputs/") and \
                (self.path.endswith(".mp4") or self.path.endswith(".jpg")):
            name = os.path.basename(self.path)
            path = os.path.join(OUT, name)
            if not os.path.exists(path):
                return self._json(404, {"error": "not found"})
            data = open(path, "rb").read()
            self.send_response(200)
            self.send_header("Content-Type",
                             "video/mp4" if name.endswith(".mp4")
                             else "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        try:
            if self.path == "/api/script":
                b = self._body()
                mode = b.get("mode", "demo")
                brand = (b.get("brand") or "")[:40]
                if mode == "groq":
                    if not b.get("api_key"):
                        return self._json(400, {
                            "error": "Groq API key missing — paste your "
                                     "free key, or use Demo mode."})
                    script = generators.groq_generate(
                        b.get("prompt", ""), b["api_key"], brand)
                elif mode == "paste":
                    script = generators.paste_generate(
                        b.get("text", ""), brand)
                else:
                    script = generators.demo_generate(
                        b.get("prompt", ""), brand)
                self._json(200, {"script": script})
            elif self.path == "/api/render":
                b = self._body()
                script = b.get("script") or {}
                if not script.get("scenes"):
                    return self._json(400, {"error": "script has no scenes"})
                job_id = uuid.uuid4().hex[:10]
                opts = b.get("options") or {}
                opts = {"voice": opts.get("voice", "hi"),
                        "music": bool(opts.get("music", False)),
                        "speed": float(opts.get("speed", 0.9))}
                with LOCK:
                    JOBS[job_id] = {"status": "rendering", "stage": "voice",
                                    "done": 0, "total": 0, "video": None,
                                    "cover": None, "error": None,
                                    "meta": None}
                threading.Thread(target=run_job,
                                 args=(job_id, script, opts),
                                 daemon=True).start()
                self._json(200, {"job_id": job_id})
            else:
                self._json(404, {"error": "not found"})
        except Exception as e:
            self._json(500, {"error": str(e)[:400]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Prompt2Video on http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
