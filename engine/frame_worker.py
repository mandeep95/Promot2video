"""
Frame-chunk worker: renders frames [start, end) of a planned job.

Runs as a fresh subprocess per chunk so every byte of PIL memory is
returned to the OS when it exits — the web server process itself never
grows, which is what keeps long renders alive on a 512MB free instance.
Reads workdir/render_plan.json (written by renderer.render), writes
fNNNNN.png files into workdir/frames, prints "P <done> <total>" lines.
"""

import gc
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
import renderer as R  # noqa: E402  (scene functions + constants)


def main():
    workdir, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    plan = json.load(open(os.path.join(workdir, "render_plan.json")))
    scenes = plan["scenes"]
    layout = plan["layout"]  # [{"scene": idx, "frames": n}, ...]
    fdir = os.path.join(workdir, "frames")
    os.makedirs(fdir, exist_ok=True)

    spans, off = [], 0
    for li, lay in enumerate(layout):
        spans.append((off, off + lay["frames"], li))
        off += lay["frames"]
    total = off

    def locate(n):
        for s, e, li in spans:
            if s <= n < e:
                return li, n - s
        raise IndexError(n)

    n = a
    while n < b:
        li, lt = locate(n)
        lay = layout[li]
        sc = scenes[lay["scene"]]
        L = lay["frames"]
        img = R.SCENES[sc["visual"]](lt, L, sc)
        if lt > L - R.FADE and li < len(layout) - 1:
            nlay = layout[li + 1]
            nsc = scenes[nlay["scene"]]
            img = Image.blend(
                img, R.SCENES[nsc["visual"]](
                    lt - (L - R.FADE), nlay["frames"], nsc),
                (lt - (L - R.FADE)) / R.FADE)
        img.save(os.path.join(fdir, f"f{n:05d}.png"))
        img.close()
        n += 1
        if n % 30 == 0 or n == b:
            print(f"P {n} {total}", flush=True)
        if n % 120 == 0:
            gc.collect()
    print(f"DONE {b}", flush=True)


if __name__ == "__main__":
    main()
