"""
Proof scene: BalakheJi-style full STORY reel, 100% code.

Flat 2D vector characters + props drawn from shapes (no images, no AI):
  Scene 1 (0-6s)   The old setup   — stall, bench, regular customers, steam
  Scene 2 (6-12s)  The abrupt change — NAYA SYSTEM board, QR-only, bench gone,
                   customers walk away, vendor worried
  Scene 3 (12-18s) The gradual fix — bench back, CASH + ONLINE, customers
                   return, one scans QR happily, vendor pours chai

Same f(t) rule as always: render(t) is pure. Subtitles are dark pills with
yellow keyword highlights, like the reference. Silent — narration is a
separate audio step (TTS / recorded voice mixed with ffmpeg).

Run: python3 proof_scene.py  -> proof-scene.mp4
"""

import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
SCENE_LEN = FPS * 6          # 6s per scene
N = SCENE_LEN * 3            # 18s total
FADE = 12                    # crossfade frames between scenes
HERE = os.path.dirname(os.path.abspath(__file__))

_FONTDIR = os.path.normpath(os.path.join(HERE, "..", "fonts"))
F_BLACK = os.path.join(_FONTDIR, "NotoSansDisplay-Black.ttf")
F_BOLD = os.path.join(_FONTDIR, "NotoSans-Bold.ttf")
F_SEMI = os.path.join(_FONTDIR, "NotoSansDisplay-SemiBold.ttf")
F_SERIF = os.path.join(_FONTDIR, "NotoSerif-Regular.ttf")


def _pick_font(path, *patterns):
    """Font robustness across machines/images: if the exact file is
    missing, fall back to the closest available Noto/DejaVu file."""
    import glob
    import os
    if os.path.exists(path):
        return path
    for pat in patterns:
        hits = sorted(glob.glob(pat, recursive=True))
        if hits:
            return hits[0]
    return path


F_BLACK = _pick_font(
    F_BLACK, "/usr/share/fonts/**/NotoSansDisplay-*.ttf",
    "/usr/share/fonts/**/NotoSans-Bold.ttf",
    "/usr/share/fonts/**/DejaVuSans-Bold.ttf")
F_BOLD = _pick_font(
    F_BOLD, "/usr/share/fonts/**/NotoSans-Bold.ttf",
    "/usr/share/fonts/**/NotoSansDisplay-*.ttf",
    "/usr/share/fonts/**/DejaVuSans-Bold.ttf")
F_SEMI = _pick_font(
    F_SEMI, "/usr/share/fonts/**/NotoSansDisplay-*.ttf",
    "/usr/share/fonts/**/NotoSans-Bold.ttf",
    "/usr/share/fonts/**/DejaVuSans-Bold.ttf")
F_SERIF = _pick_font(
    F_SERIF, "/usr/share/fonts/**/NotoSerif-*.ttf",
    "/usr/share/fonts/**/DejaVuSerif.ttf")

# warm earthy palette (sampled from the reference's story frames)
CREAM = (243, 229, 207)
CREAM_DARK = (231, 210, 175)
GROUND = (201, 138, 90)
GROUND_DARK = (176, 116, 72)
TEAL = (20, 82, 75)
TEAL_DARK = (13, 56, 51)
TERRA = (199, 91, 57)
TERRA_DARK = (168, 70, 42)
WOOD = (122, 74, 43)
WOOD_DARK = (96, 56, 32)
INK = (43, 33, 24)
PAPER = (250, 243, 228)
RED = (192, 48, 38)
GREEN = (46, 125, 74)
YELLOW = (255, 201, 60)
PILL = (30, 25, 20)
SKIN1 = (224, 172, 105)
SKIN2 = (198, 134, 66)
SKIN3 = (141, 85, 36)
GREY_HAIR = (210, 205, 200)


def ease(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def clamp01(k):
    return max(0.0, min(1.0, k))


def lerp(a, b, k):
    return a + (b - a) * k


# ---------------------------------------------------------------- people

def face(d, cx, cy, r, mood="happy"):
    """Eyes + mouth on a head circle centred (cx, cy)."""
    er = max(3, r // 9)
    for ex in (cx - r // 3, cx + r // 3):
        d.ellipse([ex - er, cy - er - 2, ex + er, cy + er - 2], fill=INK)
    if mood == "happy":
        d.arc([cx - r // 3, cy + r // 8, cx + r // 3, cy + r // 2 + 6],
              start=15, end=165, fill=INK, width=5)
    elif mood == "sad":
        d.arc([cx - r // 3, cy + r // 4, cx + r // 3, cy + r // 2 + 8],
              start=195, end=345, fill=INK, width=5)
    else:
        d.line([cx - r // 4, cy + r // 3, cx + r // 4, cy + r // 3],
               fill=INK, width=5)


def head(d, cx, cy, r, skin, hair=INK, mood="happy", cap=None):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=skin)
    # hair: top cap
    d.pieslice([cx - r, cy - r - 4, cx + r, cy + r // 2], start=180, end=360,
               fill=hair)
    if cap:
        d.pieslice([cx - r - 6, cy - r - 6, cx + r + 6, cy + r // 3],
                   start=180, end=360, fill=cap)
        d.rectangle([cx - r - 14, cy - r // 4, cx + r + 14, cy - r // 4 + 10],
                    fill=cap)
    face(d, cx, cy + r // 8, r, mood)


def person_standing(d, x, ground_y, s, skin, shirt, pants, hair=INK,
                    mood="happy", bob=0, walk_phase=None, hold=None,
                    arm_down=True):
    """Standing figure, feet at ground_y, height ~ 300*s."""
    y = ground_y + bob
    hip_y = y - 105 * s
    sh_y = y - 215 * s            # shoulder
    head_cy = sh_y - 52 * s
    # legs
    if walk_phase is not None:
        sw = math.sin(walk_phase) * 26 * s
        d.line([x - 16 * s, hip_y, x - 16 * s + sw, y - 8], fill=pants,
               width=int(26 * s))
        d.line([x + 16 * s, hip_y, x + 16 * s - sw, y - 8], fill=pants,
               width=int(26 * s))
    else:
        d.rectangle([x - 30 * s, hip_y, x - 4 * s, y - 6], fill=pants)
        d.rectangle([x + 4 * s, hip_y, x + 30 * s, y - 6], fill=pants)
    d.ellipse([x - 40 * s, y - 12, x - 2 * s, y + 4], fill=INK)   # shoes
    d.ellipse([x + 2 * s, y - 12, x + 40 * s, y + 4], fill=INK)
    # torso
    d.rounded_rectangle([x - 46 * s, sh_y, x + 46 * s, hip_y + 14 * s],
                        radius=int(18 * s), fill=shirt)
    # arms
    if hold == "phone":
        d.line([x + 44 * s, sh_y + 22 * s, x + 74 * s, sh_y + 78 * s],
               fill=shirt, width=int(20 * s))
        d.rectangle([x + 62 * s, sh_y + 52 * s, x + 92 * s, sh_y + 108 * s],
                    fill=INK)
        d.rectangle([x + 66 * s, sh_y + 58 * s, x + 88 * s, sh_y + 96 * s],
                    fill=(170, 220, 235))
        d.line([x - 44 * s, sh_y + 22 * s, x - 58 * s, hip_y + 6 * s],
               fill=shirt, width=int(20 * s))
    elif hold == "cash":
        d.line([x + 44 * s, sh_y + 22 * s, x + 76 * s, sh_y + 66 * s],
               fill=shirt, width=int(20 * s))
        d.rectangle([x + 58 * s, sh_y + 44 * s, x + 104 * s, sh_y + 76 * s],
                    fill=(92, 168, 96), outline=INK, width=3)
        d.line([x - 44 * s, sh_y + 22 * s, x - 58 * s, hip_y + 6 * s],
               fill=shirt, width=int(20 * s))
    elif hold == "cup":
        d.line([x + 44 * s, sh_y + 22 * s, x + 68 * s, sh_y + 84 * s],
               fill=shirt, width=int(20 * s))
        d.rectangle([x + 58 * s, sh_y + 76 * s, x + 88 * s, sh_y + 106 * s],
                    fill=PAPER, outline=INK, width=3)
        d.line([x - 44 * s, sh_y + 22 * s, x - 58 * s, hip_y + 6 * s],
               fill=shirt, width=int(20 * s))
    elif arm_down:
        d.line([x - 44 * s, sh_y + 22 * s, x - 60 * s, hip_y + 8 * s],
               fill=shirt, width=int(20 * s))
        d.line([x + 44 * s, sh_y + 22 * s, x + 60 * s, hip_y + 8 * s],
               fill=shirt, width=int(20 * s))
    head(d, x, head_cy, int(38 * s), skin, hair, mood)


def person_sitting(d, x, bench_y, s, skin, shirt, pants, hair=INK,
                   mood="happy", cup=False, bob=0, hold=None):
    """Sitting figure on a bench whose seat is at bench_y."""
    seat = bench_y + bob
    sh_y = seat - 150 * s
    head_cy = sh_y - 50 * s
    # legs: thigh forward, shin down
    d.rectangle([x - 8 * s, seat - 16 * s, x + 74 * s, seat + 8 * s],
                fill=pants)
    d.rectangle([x + 52 * s, seat, x + 76 * s, seat + 92 * s], fill=pants)
    d.ellipse([x + 46 * s, seat + 86 * s, x + 88 * s, seat + 102 * s],
              fill=INK)
    # torso
    d.rounded_rectangle([x - 44 * s, sh_y, x + 44 * s, seat + 6],
                        radius=int(16 * s), fill=shirt)
    if cup:
        d.line([x + 42 * s, sh_y + 24 * s, x + 72 * s, sh_y + 76 * s],
               fill=shirt, width=int(19 * s))
        d.rectangle([x + 62 * s, sh_y + 68 * s, x + 92 * s, sh_y + 98 * s],
                    fill=PAPER, outline=INK, width=3)
    elif hold == "phone":   # arm raised, phone up toward the QR stand
        d.line([x + 42 * s, sh_y + 24 * s, x + 84 * s, sh_y - 6 * s],
               fill=shirt, width=int(19 * s))
        d.rectangle([x + 76 * s, sh_y - 44 * s, x + 108 * s, sh_y + 14 * s],
                    fill=INK)
        d.rectangle([x + 80 * s, sh_y - 38 * s, x + 104 * s, sh_y + 2 * s],
                    fill=(170, 220, 235))
    elif hold == "cash":
        d.line([x + 42 * s, sh_y + 24 * s, x + 78 * s, sh_y + 62 * s],
               fill=shirt, width=int(19 * s))
        d.rectangle([x + 62 * s, sh_y + 42 * s, x + 112 * s, sh_y + 76 * s],
                    fill=(92, 168, 96), outline=INK, width=3)
    else:
        d.line([x + 42 * s, sh_y + 24 * s, x + 60 * s, seat - 8 * s],
               fill=shirt, width=int(19 * s))
    d.line([x - 42 * s, sh_y + 24 * s, x - 56 * s, seat - 8 * s],
           fill=shirt, width=int(19 * s))
    head(d, x, head_cy, int(37 * s), skin, hair, mood)


def vendor(d, cx, counter_top, s, mood="happy", pour=False, lt=0):
    """Vendor upper body behind the counter at counter_top."""
    sh_y = counter_top - 150 * s
    head_cy = sh_y - 52 * s
    d.rounded_rectangle([cx - 58 * s, sh_y, cx + 58 * s, counter_top + 30],
                        radius=int(20 * s), fill=TERRA)
    # apron stripe
    d.rectangle([cx - 58 * s, sh_y + 74 * s, cx + 58 * s, sh_y + 96 * s],
                fill=CREAM)
    if pour:
        # right arm out holding a tilted kettle, stream into a cup
        d.line([cx + 54 * s, sh_y + 26 * s, cx + 128 * s, sh_y + 40 * s],
               fill=TERRA, width=int(21 * s))
        kx, ky = cx + 150 * s, sh_y + 18 * s
        d.ellipse([kx - 36 * s, ky, kx + 36 * s, ky + 50 * s], fill=INK)
        d.ellipse([kx - 22 * s, ky + 8 * s, kx + 2 * s, ky + 24 * s],
                  fill=(92, 84, 76))
        d.arc([kx - 24 * s, ky - 22 * s, kx + 24 * s, ky + 16 * s],
              180, 360, fill=INK, width=int(6 * s))
        d.polygon([(kx + 28 * s, ky + 14 * s), (kx + 58 * s, ky + 30 * s),
                   (kx + 30 * s, ky + 36 * s)], fill=INK)
        stream_top = ky + 52 * s
        cup_y = counter_top - 36 * s
        dash = int((lt % 12))
        yy = stream_top
        while yy < cup_y:
            d.line([kx + 52 * s, yy, kx + 52 * s, min(yy + 9, cup_y)],
                   fill=(255, 190, 90), width=5)
            yy += 16
        d.rectangle([kx + 34 * s, cup_y, kx + 72 * s, cup_y + 36 * s],
                    fill=PAPER, outline=INK, width=3)
        d.line([cx - 54 * s, sh_y + 26 * s, cx - 70 * s, counter_top - 6],
               fill=TERRA, width=int(21 * s))
    elif mood == "sad":
        # crossed arms
        d.line([cx - 50 * s, sh_y + 40 * s, cx + 46 * s, sh_y + 108 * s],
               fill=TERRA_DARK, width=int(21 * s))
        d.line([cx + 50 * s, sh_y + 40 * s, cx - 46 * s, sh_y + 108 * s],
               fill=TERRA_DARK, width=int(21 * s))
    else:
        d.line([cx - 54 * s, sh_y + 26 * s, cx - 76 * s, counter_top - 4],
               fill=TERRA, width=int(21 * s))
        d.line([cx + 54 * s, sh_y + 26 * s, cx + 76 * s, counter_top - 4],
               fill=TERRA, width=int(21 * s))
    head(d, cx, head_cy, int(42 * s), SKIN2, INK, mood, cap=CREAM)


# ---------------------------------------------------------------- props

def steam(d, x, y, lt, n=3, h=74):
    for i in range(n):
        sx = x + i * 26 - (n - 1) * 13
        pts = []
        for j in range(13):
            yy = y - j * (h / 12)
            xx = sx + math.sin(lt / 9 + j / 2.2 + i * 1.7) * 8
            pts.append((xx, yy))
        d.line(pts, fill=(255, 255, 255, 170), width=6)


def kettle(d, x, y, s=1.0, lt=0):
    d.ellipse([x - 46 * s, y - 30 * s, x + 46 * s, y + 34 * s], fill=INK)
    d.polygon([(x - 44 * s, y - 8 * s), (x - 74 * s, y + 8 * s),
               (x - 42 * s, y + 18 * s)], fill=INK)
    d.arc([x - 30 * s, y - 62 * s, x + 30 * s, y - 8 * s], 180, 360,
          fill=INK, width=int(7 * s))
    steam(d, x, y - 66 * s, lt, n=2, h=58)


def qr_code(d, x, y, size):
    """Deterministic QR-looking pattern (fixed matrix, no randomness)."""
    d.rectangle([x, y, x + size, y + size], fill=(255, 255, 255),
                outline=INK, width=4)
    cell = size / 12
    pattern = ("111111101011", "100010100110", "101110111010",
               "101110100111", "100010101010", "111111110101",
               "000000101110", "110101011001", "001110100110",
               "101011101011", "110100011101", "101101110100")
    for r, row in enumerate(pattern):
        for c, v in enumerate(row):
            if v == "1":
                d.rectangle([x + c * cell, y + r * cell,
                             x + (c + 1) * cell, y + (r + 1) * cell],
                            fill=INK)
    for (fx, fy) in ((0, 0), (8, 0), (0, 8)):    # finder squares re-drawn
        d.rectangle([x + fx * cell, y + fy * cell, x + (fx + 4) * cell,
                     y + (fy + 4) * cell], fill=(255, 255, 255))
        d.rectangle([x + fx * cell, y + fy * cell, x + (fx + 4) * cell,
                     y + (fy + 4) * cell], outline=INK, width=4)
        d.rectangle([x + (fx + 1) * cell, y + (fy + 1) * cell,
                     x + (fx + 3) * cell, y + (fy + 3) * cell], fill=INK)


def stall(lt, bench=True, qr_stand=False, board=None, mood="happy",
          pour=False):
    """Full stall scene background + vendor. Ground line at y=1420."""
    img = Image.new("RGB", (W, H), CREAM)
    dr = ImageDraw.Draw(img, "RGBA")
    # back wall + ground
    dr.rectangle([0, 300, W, 1420], fill=CREAM_DARK)
    dr.rectangle([0, 1420, W, H], fill=GROUND)
    dr.rectangle([0, 1420, W, 1446], fill=GROUND_DARK)
    # stall frame
    sx0, sx1, top = 90, 990, 430
    dr.rectangle([sx0, top, sx0 + 26, 1420], fill=WOOD_DARK)
    dr.rectangle([sx1 - 26, top, sx1, 1420], fill=WOOD_DARK)
    dr.rectangle([sx0, top + 120, sx1, 1420], fill=TEAL)     # back panel
    # awning: striped with scalloped edge
    for i in range(10):
        col = TERRA if i % 2 == 0 else PAPER
        ax = sx0 - 30 + i * 96
        dr.rectangle([ax, top - 96, ax + 96, top + 8], fill=col)
        dr.pieslice([ax, top - 26, ax + 96, top + 44], 0, 180, fill=col)
    dr.rectangle([sx0 - 30, top - 110, sx1 + 30, top - 84], fill=WOOD_DARK)
    # sign
    f_sign = ImageFont.truetype(F_BOLD, 58)
    sign_w = dr.textlength("Vijay ki Chai", font=f_sign) + 90
    cx = (sx0 + sx1) / 2
    dr.rounded_rectangle([cx - sign_w / 2, top + 158, cx + sign_w / 2,
                          top + 262], radius=18, fill=PAPER)
    dr.text((cx - sign_w / 2 + 45, top + 180), "Vijay ki Chai",
            font=f_sign, fill=INK)
    # counter
    c_top = 1050
    dr.rectangle([sx0 + 60, c_top, sx1 - 60, 1420], fill=WOOD)
    dr.rectangle([sx0 + 40, c_top - 18, sx1 - 40, c_top + 16], fill=WOOD_DARK)
    for gx in range(int(sx0 + 130), int(sx1 - 90), 150):
        dr.line([gx, c_top + 40, gx, 1396], fill=WOOD_DARK, width=6)
    # vendor behind counter
    vendor(dr, cx - 190, c_top - 16, 1.25, mood=mood, pour=pour, lt=lt)
    # on the counter: kettle (unless the vendor is holding it) + cups + jar
    if not pour:
        kettle(dr, cx + 60, c_top - 58, 1.0, lt)
    for i in range(3):
        dr.rectangle([cx + 196 + i * 8, c_top - 52 - i * 26,
                      cx + 240 + i * 8, c_top - 28 - i * 26],
                     fill=PAPER, outline=INK, width=3)
    dr.rounded_rectangle([cx + 300, c_top - 108, cx + 386, c_top - 20],
                         radius=12, fill=(240, 220, 170, 235), outline=INK,
                         width=3)
    dr.ellipse([cx + 316, c_top - 84, cx + 344, c_top - 44],
               fill=TERRA)
    dr.ellipse([cx + 342, c_top - 92, cx + 370, c_top - 52],
               fill=TERRA_DARK)
    if qr_stand:
        qr_code(dr, cx + 120, c_top - 210, 128)
        dr.rectangle([cx + 176, c_top - 82, cx + 192, c_top - 18],
                     fill=INK)
        dr.rectangle([cx + 138, c_top - 30, cx + 230, c_top - 14],
                     fill=INK)
    if bench:
        by = 1560
        dr.rectangle([170, by, 910, by + 34], fill=WOOD)
        dr.rectangle([170, by + 66, 910, by + 92], fill=WOOD)
        for bx in (210, 830):
            dr.rectangle([bx, by + 34, bx + 30, by + 210], fill=WOOD_DARK)
    if board:
        board(dr)
    return img


def subtitle(img, lt, segments, delay=10):
    """Dark pill, bottom centre; segments = [(text, is_highlight), ...]."""
    k = ease((lt - delay) / 12)
    if k <= 0:
        return img
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(F_BOLD, 41)
    widths = [d.textlength(txt, font=f) for txt, _ in segments]
    total = sum(widths)
    pw, ph = total + 72, 92
    x0 = (W - pw) / 2
    y0 = 1690 + int(26 * (1 - k))
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=46,
                        fill=PILL + (int(235 * k),))
    x = x0 + 36
    for (txt, hi), tw in zip(segments, widths):
        d.text((x, y0 + 22), txt, font=f,
               fill=(YELLOW if hi else (245, 240, 230)) + (int(255 * k),))
        x += tw
    return img


def law_badge(img):
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(F_SEMI, 38)
    tw = d.textlength("LAW 45", font=f)
    d.rounded_rectangle([W - tw - 110, 64, W - 54, 128], radius=32,
                        fill=TEAL_DARK + (255,))
    d.text((W - tw - 82, 76), "LAW 45", font=f, fill=CREAM)
    return img


def big_title(img, lt, text):
    k = ease(lt / 16)
    if k <= 0:
        return img
    d = ImageDraw.Draw(img, "RGBA")
    f = ImageFont.truetype(F_BLACK, 92)
    y = 128 + int(30 * (1 - k))
    d.text((70, y), text, font=f, fill=INK + (int(255 * k),))
    d.rectangle([74, y + 118, 74 + int(120 * k), y + 128],
                fill=TERRA + (int(255 * k),))
    return img


# ---------------------------------------------------------------- scenes

def scene1(lt):
    img = stall(lt, bench=True, mood="happy")
    d = ImageDraw.Draw(img, "RGBA")
    bob1 = int(math.sin(lt / 14) * 4)
    bob2 = int(math.sin(lt / 14 + 2) * 4)
    person_sitting(d, 330, 1560, 1.05, SKIN1, TEAL, (70, 60, 90),
                   cup=True, bob=bob1)
    person_sitting(d, 640, 1560, 1.05, SKIN3, (214, 164, 65), TEAL_DARK,
                   hair=GREY_HAIR, bob=bob2)
    img = big_title(img, lt, "Wahi chai.")
    img = law_badge(img)
    img = subtitle(img, lt, [("Wahi bench, ", False), ("roz ke", True),
                             (" graahak.", False)])
    return img


def scene2_board(d):
    """Freestanding poster board in the foreground, left of the counter."""
    x0, y0, x1, y1 = 64, 996, 648, 1436
    d.rectangle([x0 + 72, y1, x0 + 98, y1 + 86], fill=WOOD_DARK)
    d.rectangle([x1 - 98, y1, x1 - 72, y1 + 86], fill=WOOD_DARK)
    d.rounded_rectangle([x0 + 14, y0 + 18, x1 + 14, y1 + 18], radius=16,
                        fill=(0, 0, 0, 60))
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=PAPER)
    f_big = ImageFont.truetype(F_BLACK, 62)
    f_mid = ImageFont.truetype(F_BOLD, 41)
    d.text((x0 + 42, y0 + 34), "NAYA SYSTEM", font=f_big, fill=RED)
    d.line([x0 + 42, y0 + 118, x1 - 42, y0 + 118], fill=INK, width=4)
    d.text((x0 + 42, y0 + 146), "ORDER: SIRF QR SCAN", font=f_mid, fill=INK)
    d.text((x0 + 42, y0 + 208), "PAYMENT: SIRF ONLINE", font=f_mid,
           fill=INK)
    d.text((x0 + 42, y0 + 292), "CASH NAHI", font=f_mid, fill=RED)
    cx, cy, r = x0 + 448, y0 + 316, 38
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED, width=9)
    d.line([cx - 24, cy - 24, cx + 24, cy + 24], fill=RED, width=9)
    d.line([cx + 24, cy - 24, cx - 24, cy + 24], fill=RED, width=9)


def scene2(lt):
    img = stall(lt, bench=False, qr_stand=True, mood="sad")
    scene2_board(ImageDraw.Draw(img, "RGBA"))
    d = ImageDraw.Draw(img, "RGBA")
    # customers walk away to the right and off-frame
    k = clamp01(lt / (SCENE_LEN * 0.92))
    base = lerp(560, 1240, ease(k))
    bob = abs(math.sin(lt / 5.2)) * -10
    person_standing(d, base, 1620, 1.05, SKIN1, TEAL, (70, 60, 90),
                    mood="sad", bob=bob, walk_phase=lt / 5.2)
    person_standing(d, base - 240, 1660, 1.0, SKIN3, (214, 164, 65),
                    TEAL_DARK, hair=GREY_HAIR, mood="sad",
                    bob=abs(math.sin(lt / 5.2 + 1.4)) * -10,
                    walk_phase=lt / 5.2 + 1.4)
    img = big_title(img, lt, "Sab badal diya.")
    img = law_badge(img)
    img = subtitle(img, lt, [("Sab kuch ", False), ("ek din me", True),
                             (" badla — graahak gayab.", False)])
    return img


def draw_check(d, cx, cy, col, s=1.0):
    d.line([cx - 13 * s, cy, cx - 4 * s, cy + 10 * s], fill=col,
           width=int(6 * s))
    d.line([cx - 4 * s, cy + 10 * s, cx + 15 * s, cy - 12 * s], fill=col,
           width=int(6 * s))


def scene3_sign(d):
    """Board fixed on the counter front — no clash with the QR stand."""
    x0, y0, x1, y1 = 300, 1136, 780, 1288
    d.rounded_rectangle([x0 + 10, y0 + 12, x1 + 10, y1 + 12], radius=16,
                        fill=(0, 0, 0, 60))
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=TEAL_DARK)
    f = ImageFont.truetype(F_BOLD, 39)
    title = "CASH + ONLINE"
    tw = d.textlength(title, font=f)
    d.text((x0 + (480 - tw) / 2, y0 + 14), title, font=f, fill=CREAM)
    f_pill = ImageFont.truetype(F_BOLD, 30)
    for i, (label, col) in enumerate((("Cash", GREEN),
                                       ("Online", TEAL_DARK))):
        lx = x0 + 24 + i * 222
        d.rounded_rectangle([lx, y0 + 72, lx + 210, y0 + 126], radius=27,
                            fill=PAPER)
        fw = d.textlength(label, font=f_pill)
        d.text((lx + 20, y0 + 84), label, font=f_pill, fill=col)
        draw_check(d, lx + 44 + fw + 16, y0 + 99, col, 0.9)


def scene3(lt):
    img = stall(lt, bench=True, qr_stand=True, mood="happy", pour=True)
    scene3_sign(ImageDraw.Draw(img, "RGBA"))
    d = ImageDraw.Draw(img, "RGBA")
    # full circle: the regulars are back on the bench — one happily
    # scans the QR with his phone, the other still pays cash.
    bob1 = int(math.sin(lt / 14) * 4)
    bob2 = int(math.sin(lt / 14 + 2) * 4)
    person_sitting(d, 330, 1560, 1.05, SKIN1, TEAL, (70, 60, 90),
                   bob=bob1, hold="phone")
    person_sitting(d, 640, 1560, 1.05, SKIN3, (214, 164, 65), TEAL_DARK,
                   hair=GREY_HAIR, bob=bob2, hold="cash")
    img = big_title(img, lt, "Dheere-dheere sahi.")
    img = law_badge(img)
    img = subtitle(img, lt, [("Badlav ", False), ("dheere-dheere", True),
                             (" aaya, sab jud gaye.", False)])
    return img


SCENES = (scene1, scene2, scene3)


def render(t):
    idx = min(t // SCENE_LEN, 2)
    lt = t - idx * SCENE_LEN
    img = SCENES[idx](lt)
    # crossfade into the next scene
    if lt > SCENE_LEN - FADE and idx < 2:
        k = (lt - (SCENE_LEN - FADE)) / FADE
        nxt = SCENES[idx + 1](lt - (SCENE_LEN - FADE))
        img = Image.blend(img, nxt, k)
    return img


def main():
    frames = os.path.join(HERE, "proof_frames")
    os.makedirs(frames, exist_ok=True)
    for t in range(N):
        render(t).save(os.path.join(frames, f"f{t:04d}.png"))
        if t % 90 == 0:
            print(f"frame {t}/{N-1}", flush=True)
    out = os.path.join(HERE, "proof-scene.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(frames, "f%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-movflags", "+faststart", out,
    ], check=True, capture_output=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
