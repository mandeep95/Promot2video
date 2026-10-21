"""
Background music, synthesized with pure Python (no files, no licenses).

A soft lo-fi loop: Am–F–C–G pad chords (sine + harmonic, slow attack)
with gentle pentatonic plucks on top. Generated per-render at exactly
the video's length, then mixed low under the narration.
"""

import math
import struct
import wave

SR = 22050
CHORDS = [  # (name, [freqs]) — Am, F, C, G, 2.4s each
    ("Am", [220.00, 261.63, 329.63]),
    ("F", [174.61, 220.00, 261.63]),
    ("C", [196.00, 261.63, 329.63]),
    ("G", [196.00, 246.94, 293.66]),
]
CHORD_LEN = 2.4
PENTA = [440.00, 523.25, 587.33, 659.25, 783.99, 880.00]
MELODY = [0, 2, 4, 3, 1, 4, 5, 4, 2, 1, 3, 2, 0, 1, 2, 4]  # indexes, 0.6s apart


def _pluck(t, freq, start):
    dt = t - start
    if dt < 0 or dt > 1.1:
        return 0.0
    env = math.exp(-dt * 4.5)
    return env * (math.sin(2 * math.pi * freq * dt)
                  + 0.35 * math.sin(4 * math.pi * freq * dt))


def make_music(path, duration):
    n = int(duration * SR)
    chord_total = CHORD_LEN * len(CHORDS)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for i in range(n):
            t = i / SR
            # pad: current chord, soft attack/release within the chord
            ci = int(t // CHORD_LEN) % len(CHORDS)
            ct = t % CHORD_LEN
            fade = min(ct / 0.5, 1.0, (CHORD_LEN - ct) / 0.5)
            s = 0.0
            for f in CHORDS[ci][1]:
                s += 0.055 * fade * (math.sin(2 * math.pi * f * t)
                                     + 0.4 * math.sin(4 * math.pi * f * t))
            # plucks
            step = int(t // 0.6)
            for st in (step - 1, step):
                if 0 <= st < len(MELODY) * 999:
                    s += 0.10 * _pluck(t, PENTA[MELODY[st % len(MELODY)]],
                                       st * 0.6)
            # gentle master fade in/out
            g = min(t / 1.2, 1.0, max(0.0, (duration - t) / 1.5))
            v = max(-1.0, min(1.0, s * g))
            frames += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(frames))
    return path
