---
title: Prompt2Video
emoji: 🎬
colorFrom: indigo
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# Prompt2Video — Prompt likho, Code banayega, Video milega

A website where you type a **prompt** (or paste your own script/screen
text), a **free AI** turns it into a story script (JSON scene-code), and a
**code renderer** turns that script into a finished vertical MP4 with
Hindi narration — the BalakheJi-style flat-animation format. No AI-video
credits, no editor. Cost per video: ₹0.

## Flow

```
Prompt / pasted script
   → (Groq free AI  |  Demo generator  |  Paste parser)   → script JSON
   → Piper TTS (local, free)                              → Hindi voice
   → PIL f(t) renderer (engine/)                          → frames
   → ffmpeg                                               → MP4 1080×1920
```

## Run locally

```bash
# needs: python3, ffmpeg, Piper binary + hi_IN-rohan voice
# (defaults: ~/workspace/code-video/piper/... or set env vars)
P2V_PIPER_BIN=/path/to/piper P2V_PIPER_MODEL=/path/to/hi_IN-rohan-medium.onnx \
  PORT=8000 python3 server.py
# open http://localhost:8000
```

## Modes

| Mode | Key needed | What happens |
|---|---|---|
| Free AI (Groq) | User's own free Groq key (browser-local only, never stored server-side) | llama-3.3-70b writes an original 6–7 scene Hindi story script |
| Demo | none | Rule-based generator (Law 1/3/6/15/28/45 built in, generic topics supported) |
| Paste script | none | Each paragraph of your text becomes a scene; a moral card is appended |

Every script is **editable in the browser** (headline, narration, subtitle,
highlight word, visual style per scene) before rendering.

## Render options

- **Voice:** Hindi male (Piper Rohan) or English female (Piper Amy)
- **Speed:** Tez / Normal / Dheere (Piper length-scale 0.84 / 0.9 / 1.0)
- **Background music:** a soft instrumental loop synthesized in code
  (`engine/music.py` — Am–F–C–G pad + pentatonic plucks), mixed low
  under the narration. No audio files, no licenses.
- Every render also produces a **cover JPG** and a **history entry**
  (the site lists previous videos with cover, duration, play/download).

## Scene templates (12)

`stall_happy, stall_idea, stall_board, stall_empty, stall_talk,
stall_gradual, stall_result` (the chai-stall story set), `quote`,
`card` (big-text cards), `phone_closeup` (QR scan animation),
`split_compare` (before/after panels), `growth_chart` (rising bars).

## Files

- `server.py` — stdlib HTTP server + job queue (no dependencies)
- `web/index.html` — the whole frontend, one file
- `engine/generators.py` — demo / Groq / paste script generators
- `engine/renderer.py` — script JSON → MP4 (scene templates + TTS sync)
- `engine/lib.py` — flat character/prop drawing library
- `outputs/` — rendered videos land here

## Deploy free (pick one)

**Hugging Face Spaces (recommended, free):** create a Docker Space with
this repo + the `Dockerfile` here. Free tier = 2 vCPU / 16 GB, sleeps
after 48h idle. Renders take ~1 min per 10 s of video there.

**Render free:** works, but 0.1 CPU makes renders very slow and the
service sleeps — fine for a private demo, not for public users.

**Your own laptop:** `python3 server.py` + any tunnel (cloudflared /
ngrok free) if you want a public link.

> Note: Vercel/Netlify alone cannot host the renderer (no long-running
> jobs / ffmpeg). Host the whole app on one of the above instead.

## Limits (honest)

- Narration is Hindi TTS (Piper, Rohan male voice). English voice =
  drop an en_US Piper model next to the Hindi one and switch
  `P2V_PIPER_MODEL`.
- One render at a time per server process is comfortable on free CPUs;
  the job API already queues via threads.
- Visual vocabulary is the chai-stall story set + quote/card scenes —
  new scene types are new functions in `engine/renderer.py`.
