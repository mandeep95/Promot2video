"""
Prompt2Video engine: script JSON -> MP4, 100% code.

Script schema:
{
  "title": "Law 45 — Sab kuch ek saath mat badlo",
  "label": "LAW 45",                # badge on story scenes
  "brand": "MyChannel",             # footer on the closing card
  "scenes": [
    {"visual": "stall_happy", "headline": "Wahi chai.",
     "narration": "<Hindi, Devanagari>", "pill": [["roz ke ", false],
                                                  ["graahak", true]]},
    ... visual in: stall_happy, stall_idea, stall_board, stall_empty,
        stall_talk (+"bubble": [l1, l2]), stall_gradual (+"checklist": []),
        stall_result, quote (+"lines": []), card (+"lines": [], "gold": 1)
  ]
}

Voice: local Piper TTS (free, offline). Paths via env P2V_PIPER_BIN /
P2V_PIPER_MODEL, else the sandbox defaults. Rendering is the f(t) rule:
every frame is a pure function of its index; ffmpeg stitches + mixes.
"""

import json
import math
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib as P  # noqa: E402  (the flat-scene library)

W, H, FPS = P.W, P.H, P.FPS
LEAD, TAIL, FADE = 0.35, 0.55, 10
INK, PAPER, TEAL, TEAL_DARK = P.INK, P.PAPER, P.TEAL, P.TEAL_DARK
TERRA, GREEN, CREAM = P.TERRA, P.GREEN, P.CREAM
GOLD = (205, 171, 110)
SKIN1, SKIN3, GREY = P.SKIN1, P.SKIN3, P.GREY_HAIR

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

PIPER_BIN = os.environ.get(
    "P2V_PIPER_BIN",
    os.path.expanduser("~/workspace/code-video/piper/piper/piper"))
PIPER_DIR = os.path.expanduser("~/workspace/code-video/piper")
VOICES = {
    "hi": os.environ.get("P2V_PIPER_MODEL",
                         os.path.join(PIPER_DIR, "hi_IN-rohan-medium.onnx")),
    "en": os.environ.get("P2V_PIPER_MODEL_EN",
                         os.path.join(PIPER_DIR, "en_US-amy-medium.onnx")),
}


# ---------------------------------------------------------------- helpers

def fit_font(d, text, path, start, min_size=54):
    size = start
    while size > min_size:
        f = ImageFont.truetype(path, size)
        if d.textlength(text, font=f) <= W - 150:
            return f
        size -= 6
    return ImageFont.truetype(path, min_size)


def title(d, lt, text):
    k = P.ease(lt / 16)
    if k <= 0 or not text:
        return
    f = fit_font(d, text, P.F_BLACK, 92)
    y = 128 + int(30 * (1 - k))
    d.text((70, y), text, font=f, fill=INK + (int(255 * k),))
    d.rectangle([74, y + 118, 74 + int(120 * k), y + 128],
                fill=TERRA + (int(255 * k),))


def badge(d, label):
    if not label:
        return
    f = ImageFont.truetype(P.F_SEMI, 38)
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([W - tw - 110, 64, W - 54, 128], radius=32,
                        fill=TEAL_DARK)
    d.text((W - tw - 82, 76), label, font=f, fill=CREAM)


def pill(img, lt, segments):
    if not segments:
        return img
    segs = [(t, bool(h)) for t, h in segments]
    return P.subtitle(img, lt + 10, segs, delay=10)


def head(img, lt, sc):
    d = ImageDraw.Draw(img, "RGBA")
    title(d, lt, sc.get("headline", ""))
    badge(d, sc.get("_label", ""))
    return pill(img, lt, sc.get("pill"))


# ---------------------------------------------------------------- scenes

def sc_stall_happy(lt, L, sc):
    img = P.stall(lt, bench=True, mood="happy")
    d = ImageDraw.Draw(img, "RGBA")
    P.person_sitting(d, 330, 1560, 1.05, SKIN1, TEAL, (70, 60, 90),
                     cup=True, bob=int(math.sin(lt / 14) * 4))
    P.person_sitting(d, 640, 1560, 1.05, SKIN3, (214, 164, 65), TEAL_DARK,
                     hair=GREY, bob=int(math.sin(lt / 14 + 2) * 4))
    return head(img, lt, sc)


def sc_stall_idea(lt, L, sc):
    img = P.stall(lt, bench=True, mood="happy")
    d = ImageDraw.Draw(img, "RGBA")
    P.person_sitting(d, 640, 1560, 1.05, SKIN3, (214, 164, 65), TEAL_DARK,
                     hair=GREY, cup=True, bob=int(math.sin(lt / 14) * 4))
    k = P.ease((lt - 25) / 14)
    if k > 0:
        bx, by, r = 292, 598, 44 * k
        for a in range(8):
            ang = a * math.pi / 4 + lt / 40
            d.line([bx + math.cos(ang) * (r + 14),
                    by + math.sin(ang) * (r + 14),
                    bx + math.cos(ang) * (r + 34),
                    by + math.sin(ang) * (r + 34)],
                   fill=(240, 180, 40, int(255 * k)), width=7)
        d.ellipse([bx - r, by - r, bx + r, by + r],
                  fill=(255, 213, 79, int(255 * k)))
        d.rectangle([bx - 15 * k, by + r - 4, bx + 15 * k, by + r + 16],
                    fill=(120, 120, 120, int(255 * k)))
        f = ImageFont.truetype(P.F_BLACK, int(52 * k) + 1)
        tw = d.textlength("!", font=f)
        d.text((bx - tw / 2, by - 30 * k), "!", font=f,
               fill=(43, 33, 24, int(255 * k)))
    return head(img, lt, sc)


def sc_stall_board(lt, L, sc):
    img = P.stall(lt, bench=False, qr_stand=True, mood="happy")
    P.scene2_board(ImageDraw.Draw(img, "RGBA"))
    d = ImageDraw.Draw(img, "RGBA")
    f_q = ImageFont.truetype(P.F_BLACK, 84)
    for x, gy, sk, sh, ph in ((790, 1640, SKIN1, TEAL, 0),
                              (960, 1690, SKIN3, (214, 164, 65), 1.6)):
        P.person_standing(d, x, gy, 1.02, sk, sh, TEAL_DARK,
                          hair=GREY if sk == SKIN3 else INK, mood="sad")
        d.text((x - 24, gy - 400 + int(math.sin(lt / 9 + ph) * 10)), "?",
               font=f_q, fill=TERRA)
    return head(img, lt, sc)


def sc_stall_empty(lt, L, sc):
    img = P.stall(lt, bench=False, mood="sad")
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = 872, 800, 74
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PAPER, outline=INK,
              width=6)
    a1, a2 = lt / 6.0, lt / 30.0
    d.line([cx, cy, cx + math.cos(a1) * 44, cy + math.sin(a1) * 44],
           fill=INK, width=7)
    d.line([cx, cy, cx + math.cos(a2) * 58, cy + math.sin(a2) * 58],
           fill=TERRA, width=5)
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=INK)
    for ph in (0, 2.6):
        fx = 350 + math.cos(lt / 7 + ph) * 78
        fy = 730 + math.sin(lt / 7 + ph) * 26
        d.ellipse([fx - 6, fy - 4, fx + 6, fy + 4], fill=INK)
    return head(img, lt, sc)


def sc_stall_talk(lt, L, sc):
    img = P.stall(lt, bench=False, mood="sad")
    d = ImageDraw.Draw(img, "RGBA")
    P.person_standing(d, 830, 1560, 1.12, SKIN3, (214, 164, 65), TEAL_DARK,
                      hair=GREY, mood="happy")
    lines = sc.get("bubble") or ["Badlav bura nahi hota,",
                                 "tareeka galat hota hai."]
    k = P.ease((lt - 28) / 12)
    if k > 0:
        a = int(255 * k)
        x0, y0, x1, y1 = 420, 716, 984, 716 + 84 + 62 * (len(lines) - 1)
        d.polygon([(786, y1 - 4), (852, y1 - 4), (836, y1 + 66)],
                  fill=PAPER + (a,))
        d.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=PAPER + (a,))
        f = ImageFont.truetype(P.F_BOLD, 43)
        for i, line in enumerate(lines[:3]):
            d.text((x0 + 36, y0 + 24 + i * 62), line, font=f,
                   fill=INK + (a,))
    return head(img, lt, sc)


def sc_stall_gradual(lt, L, sc):
    img = P.stall(lt, bench=True, qr_stand=True, mood="happy", pour=True)
    P.scene3_sign(ImageDraw.Draw(img, "RGBA"))
    d = ImageDraw.Draw(img, "RGBA")
    P.person_sitting(d, 330, 1560, 1.05, SKIN1, TEAL, (70, 60, 90),
                     bob=int(math.sin(lt / 14) * 4), hold="phone")
    P.person_sitting(d, 640, 1560, 1.05, SKIN3, (214, 164, 65), TEAL_DARK,
                     hair=GREY, bob=int(math.sin(lt / 14 + 2) * 4),
                     hold="cash")
    items = (sc.get("checklist") or
             ["Bench wapas aayi", "Cash + Online dono", "QR kone me khada"])
    x0, y0, x1 = 56, 296, 560
    y1 = y0 + 84 + len(items) * 62
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=PAPER + (242,))
    d.text((x0 + 28, y0 + 22), "STEP BY STEP",
           font=ImageFont.truetype(P.F_BOLD, 30), fill=TERRA)
    f_i = ImageFont.truetype(P.F_BOLD, 37)
    for i, item in enumerate(items):
        start = int(L * (0.16 + 0.24 * i))
        k = P.ease((lt - start) / 10)
        if k <= 0:
            continue
        iy = y0 + 74 + i * 62
        P.draw_check(d, x0 + 44, iy + 24, GREEN, 1.15)
        f2 = fit_font(d, item, P.F_BOLD, 37, 28)
        d.text((x0 + 74, iy), item, font=f2, fill=INK + (int(255 * k),))
    return head(img, lt, sc)


def sc_stall_result(lt, L, sc):
    img = P.stall(lt, bench=True, qr_stand=True, mood="happy", pour=True)
    d = ImageDraw.Draw(img, "RGBA")
    P.person_sitting(d, 330, 1560, 1.05, SKIN1, TEAL, (70, 60, 90),
                     cup=True, bob=int(math.sin(lt / 14) * 4))
    P.person_sitting(d, 640, 1560, 1.05, SKIN3, (214, 164, 65), TEAL_DARK,
                     hair=GREY, bob=int(math.sin(lt / 14 + 2) * 4),
                     hold="cash")
    P.person_standing(d, 884, 1512, 1.04, SKIN1, TERRA, (70, 60, 90),
                      hold="phone")
    k = P.ease((lt - int(L * 0.38)) / 12)
    if k > 0:
        cx, cy, r = 806, 818, int(40 * k)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        if k > 0.6:
            d.line([cx - 18, cy, cx - 5, cy + 14], fill=(255, 255, 255),
                   width=8)
            d.line([cx - 5, cy + 14, cx + 20, cy - 15],
                   fill=(255, 255, 255), width=8)
    return head(img, lt, sc)


def sc_quote(lt, L, sc):
    img = Image.new("RGB", (W, H), P.CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    lines = sc.get("lines") or [sc.get("headline", "")]
    y = 620
    for i, line in enumerate(lines[:4]):
        k = P.ease((lt - 12 - 13 * i) / 14)
        if k <= 0:
            continue
        f = fit_font(d, line, P.F_BLACK, 104)
        tw = d.textlength(line, font=f)
        col = TERRA if i == sc.get("gold", -1) else INK
        d.text(((W - tw) / 2, y + int(36 * (1 - k))), line, font=f,
               fill=col + (int(255 * k),))
        y += 138
    kr = P.ease((lt - 8) / 16)
    d.rectangle([W / 2 - int(70 * kr), 560, W / 2 + int(70 * kr), 570],
                fill=GOLD + (int(255 * kr),))
    badge(d, sc.get("_label", ""))
    return pill(img, lt, sc.get("pill"))


def sc_card(lt, L, sc):
    img = Image.new("RGB", (W, H), (11, 44, 41))
    d = ImageDraw.Draw(img, "RGBA")
    f_label = ImageFont.truetype(P.F_SEMI, 52)
    mx = 128
    label = sc.get("_label", "")
    k = P.ease(lt / 20)
    if k > 0 and label:
        x = mx
        for ch in label:
            d.text((x, 500), ch, font=f_label, fill=CREAM + (int(255 * k),))
            x += d.textlength(ch, font=f_label) + 16
        kr = P.ease((lt - 10) / 18)
        d.rectangle([mx, 590, mx + int(108 * kr), 597],
                    fill=GOLD + (int(255 * kr),))
    lines = sc.get("lines") or ["Sab kuch", "ek saath", "mat badlo."]
    gold = sc.get("gold", 1)
    for i, line in enumerate(lines[:3]):
        kk = P.ease((lt - (22 + 15 * i)) / 16)
        if kk <= 0:
            continue
        f = fit_font(d, line, P.F_BLACK, 158, 90)
        col = GOLD if i == gold else CREAM
        y = 735 + i * 205 + int(46 * (1 - kk))
        xx = mx
        for word in line.split(" "):
            d.text((xx, y), word, font=f, fill=col + (int(255 * kk),))
            xx += d.textlength(word, font=f) + 52
    ks = P.ease((lt - 80) / 20)
    brand = sc.get("_brand", "")
    if ks > 0 and brand:
        d.text((mx, 1525), brand,
               font=ImageFont.truetype(P.F_SERIF, 60),
               fill=CREAM + (int(240 * ks),))
    return img


def sc_phone(lt, L, sc):
    """Close-up: a big phone scanning a QR, scan-line sweep, success tick."""
    img = Image.new("RGB", (W, H), P.CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    # phone body
    x0, y0, x1, y1 = 240, 380, 840, 1420
    d.rounded_rectangle([x0, y0, x1, y1], radius=64, fill=(38, 34, 30))
    d.rounded_rectangle([x0 + 22, y0 + 22, x1 - 22, y1 - 22], radius=46,
                        fill=(250, 246, 236))
    d.ellipse([505, y0 + 44, 575, y0 + 66], fill=(38, 34, 30))  # camera pill
    f_app = ImageFont.truetype(P.F_BOLD, 40)
    tw = d.textlength("UPI Pay", font=f_app)
    d.text(((W - tw) / 2, y0 + 96), "UPI Pay", font=f_app, fill=INK)
    # QR on the phone screen
    P.qr_code(d, 315, 640, 450)
    # sweeping scan line inside the QR area
    sy = 640 + int((lt % 75) / 75 * 450)
    d.rectangle([315, sy - 5, 765, sy + 5], fill=TERRA + (200,))
    d.rectangle([315, sy - 26, 765, sy - 20], fill=TERRA + (70,))
    # corner brackets
    for (cx, cy, dx, dy) in ((300, 625, 1, 1), (780, 625, -1, 1),
                             (300, 1105, 1, -1), (780, 1105, -1, -1)):
        d.line([cx, cy, cx + 52 * dx, cy], fill=TEAL, width=10)
        d.line([cx, cy, cx, cy + 52 * dy], fill=TEAL, width=10)
    # success tick pops in the second half
    k = P.ease((lt - int(L * 0.52)) / 12)
    if k > 0:
        cx, cy, r = 540, 1230, int(58 * k)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        if k > 0.6:
            d.line([cx - 26, cy, cx - 7, cy + 20], fill=(255, 255, 255),
                   width=11)
            d.line([cx - 7, cy + 20, cx + 29, cy - 21],
                   fill=(255, 255, 255), width=11)
    return head(img, lt, sc)


def sc_compare(lt, L, sc):
    """Stacked before/after panels. Fields: left_title, right_title,
    left (list of short lines), right (list)."""
    img = Image.new("RGB", (W, H), P.CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    panels = [
        (sc.get("left_title", "PEHLE"), sc.get("left") or ["Cash hi chalega"],
         (196, 178, 160), TERRA, "x"),
        (sc.get("right_title", "AB"), sc.get("right") or ["Cash + Online"],
         TEAL, GREEN, "check"),
    ]
    f_t = ImageFont.truetype(P.F_BOLD, 40)
    f_l = ImageFont.truetype(P.F_BOLD, 44)
    for pi, (ptitle, lines, bg, accent, mark) in enumerate(panels):
        y0 = 330 + pi * 640
        k = P.ease((lt - 10 - pi * 22) / 14)
        if k <= 0:
            continue
        a = int(255 * k)
        d.rounded_rectangle([70, y0, W - 70, y0 + 560], radius=28,
                            fill=bg + (a,))
        d.text((110, y0 + 34), ptitle, font=f_t, fill=(255, 255, 255, a))
        for li, line in enumerate(lines[:3]):
            f2 = fit_font(d, line, P.F_BOLD, 44, 30)
            d.text((110, y0 + 140 + li * 92), line, font=f2,
                   fill=(255, 255, 255, a))
        cx, cy, r = W - 170, y0 + 400, 62
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, a))
        if mark == "check":
            d.line([cx - 28, cy, cx - 8, cy + 22], fill=GREEN, width=12)
            d.line([cx - 8, cy + 22, cx + 32, cy - 24], fill=GREEN,
                   width=12)
        else:
            d.line([cx - 24, cy - 24, cx + 24, cy + 24], fill=TERRA,
                   width=12)
            d.line([cx + 24, cy - 24, cx - 24, cy + 24], fill=TERRA,
                   width=12)
    return head(img, lt, sc)


def sc_chart(lt, L, sc):
    """Rising bar chart. Field: bars = [label, ...] up to 4."""
    img = Image.new("RGB", (W, H), P.CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    base_y, top_y = 1420, 620
    d.line([110, base_y, W - 80, base_y], fill=INK, width=6)
    d.line([110, base_y, 110, top_y - 60], fill=INK, width=6)
    labels = sc.get("bars") or ["Week 1", "Week 2", "Week 3", "Week 4"]
    labels = labels[:4]
    heights = [0.30, 0.52, 0.74, 1.0]
    cols = [(178, 160, 138), (150, 150, 140), TEAL, GOLD]
    f_lab = ImageFont.truetype(P.F_BOLD, 34)
    bw = 150
    for i, lab in enumerate(labels):
        k = P.ease((lt - 14 - i * 16) / 18)
        if k <= 0:
            continue
        h = (base_y - top_y) * heights[i] * k
        x = 190 + i * 215
        d.rounded_rectangle([x, base_y - h, x + bw, base_y], radius=14,
                            fill=cols[i])
        tw = d.textlength(lab, font=f_lab)
        d.text((x + (bw - tw) / 2, base_y + 26), lab, font=f_lab, fill=INK)
    # trend arrow across the bar tops once bars are up
    k = P.ease((lt - 90) / 16)
    if k > 0:
        x1 = 265 + (740 - 265) * k
        y1 = (base_y - (base_y - top_y) * 0.30) - 90 + \
            ((base_y - (base_y - top_y) * 1.0) - 90 -
             ((base_y - (base_y - top_y) * 0.30) - 90)) * k
        d.line([265, (base_y - (base_y - top_y) * 0.30) - 90, x1, y1],
               fill=TERRA, width=12)
        d.polygon([(x1, y1), (x1 - 42, y1 + 6), (x1 - 8, y1 + 38)],
                  fill=TERRA)
    return head(img, lt, sc)


SCENES = {
    "stall_happy": sc_stall_happy,
    "stall_idea": sc_stall_idea,
    "stall_board": sc_stall_board,
    "stall_empty": sc_stall_empty,
    "stall_talk": sc_stall_talk,
    "stall_gradual": sc_stall_gradual,
    "stall_result": sc_stall_result,
    "quote": sc_quote,
    "card": sc_card,
    "phone_closeup": sc_phone,
    "split_compare": sc_compare,
    "growth_chart": sc_chart,
}


# ---------------------------------------------------------------- render

def tts(text, wav_path, voice="hi", speed=0.9):
    model = VOICES.get(voice, VOICES["hi"])
    r = subprocess.run([PIPER_BIN, "--model", model,
                        "--length-scale", str(speed),
                        "--output_file", wav_path],
                       input=text.encode(), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("TTS failed: " + r.stderr.decode()[-300:])
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", wav_path], capture_output=True,
        text=True).stdout.strip())
    return dur


def render(script, out_mp4, workdir, on_progress=None, opts=None):
    """script dict -> MP4 at out_mp4. on_progress(stage, done, total).
    opts: {voice: 'hi'|'en', speed: float (piper length-scale),
           music: bool}"""
    opts = opts or {}
    voice = opts.get("voice", "hi")
    speed = float(opts.get("speed", 0.9))
    use_music = bool(opts.get("music", False))
    os.makedirs(workdir, exist_ok=True)
    scenes = script["scenes"]
    for sc in scenes:
        sc["_label"] = script.get("label", "")
        sc["_brand"] = script.get("brand", "")
        if sc["visual"] not in SCENES:
            sc["visual"] = "quote"
    # 1) narration per scene
    layout, t = [], 0.0
    for i, sc in enumerate(scenes):
        wav = os.path.join(workdir, f"seg{i}.wav")
        dur = tts(sc.get("narration", ""), wav, voice, speed) \
            if sc.get("narration") else 2.0
        frames = int(round((LEAD + dur + TAIL) * FPS)) \
            if sc.get("narration") else int(round(3.2 * FPS))
        layout.append({"sc": sc, "wav": wav, "frames": frames,
                       "start": t, "audio_start": t + LEAD})
        t += frames / FPS
        if on_progress:
            on_progress("voice", i + 1, len(scenes))
    total_frames = sum(s["frames"] for s in layout)
    # 2) frames
    fdir = os.path.join(workdir, "frames")
    os.makedirs(fdir, exist_ok=True)
    n = 0
    for si, lay in enumerate(layout):
        fn, L = SCENES[lay["sc"]["visual"]], lay["frames"]
        for lt in range(L):
            img = fn(lt, L, lay["sc"])
            if lt > L - FADE and si < len(layout) - 1:
                nxt = SCENES[layout[si + 1]["sc"]["visual"]]
                img = Image.blend(
                    img, nxt(lt - (L - FADE), layout[si + 1]["frames"],
                             layout[si + 1]["sc"]),
                    (lt - (L - FADE)) / FADE)
            img.save(os.path.join(fdir, f"f{n:05d}.png"))
            n += 1
            if on_progress and n % 30 == 0:
                on_progress("frames", n, total_frames)
    # 3) encode + mix
    silent = os.path.join(workdir, "silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i",
                    os.path.join(fdir, "f%05d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", silent],
                   check=True, capture_output=True)
    if on_progress:
        on_progress("mix", 1, 1)
    inputs = ["-f", "lavfi", "-t", str(t + 0.1), "-i",
              "anullsrc=cl=stereo:r=44100"]
    filters = []
    voiced = [s for s in layout if s["sc"].get("narration")]
    for i, lay in enumerate(voiced, start=1):
        inputs += ["-i", lay["wav"]]
        ms = int(lay["audio_start"] * 1000)
        filters.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[a{i}]")
    parts = ["[0:a]"] + [f"[a{i}]" for i in range(1, len(voiced) + 1)]
    if use_music:
        import music as music_mod
        mwav = os.path.join(workdir, "music.wav")
        music_mod.make_music(mwav, t + 0.2)
        mi = len(voiced) + 1
        inputs += ["-i", mwav]
        filters.append(f"[{mi}:a]aresample=44100,volume=0.5[mus]")
        parts.append("[mus]")
    if voiced or use_music:
        filters.append(
            f"{''.join(parts)}amix=inputs={len(parts)}:normalize=0[aout]")
        audio = os.path.join(workdir, "audio.m4a")
        subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex",
                        ";".join(filters), "-map", "[aout]", "-c:a", "aac",
                        "-b:a", "160k", audio],
                       check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-i", silent, "-i", audio,
                        "-c:v", "copy", "-c:a", "copy", "-shortest",
                        out_mp4], check=True, capture_output=True)
    else:
        shutil.copy(silent, out_mp4)
    shutil.rmtree(fdir, ignore_errors=True)
    return {"duration": round(t, 1), "frames": total_frames,
            "scenes": len(scenes)}
