#!/usr/bin/env bash
# Render build: the free Python image has no ffmpeg and no Piper,
# so fetch static/userland copies into .bin/ at build time.
set -e
pip install pillow

mkdir -p .bin

# ffmpeg + ffprobe (static build)
curl -sL -o /tmp/ffmpeg.tar.xz \
  https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xJf /tmp/ffmpeg.tar.xz -C .bin --strip-components=1

# Piper TTS binary
curl -sL -o /tmp/piper.tar.gz \
  https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
tar -xzf /tmp/piper.tar.gz -C .bin

# Voices: Hindi male (Rohan) + English female (Amy)
curl -sL -o .bin/hi_IN-rohan-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx
curl -sL -o .bin/hi_IN-rohan-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx.json
curl -sL -o .bin/en_US-amy-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx
curl -sL -o .bin/en_US-amy-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json

# Fonts (full versions with ₹ + Devanagari — repo carries no binaries)
mkdir -p fonts /tmp/fz
curl -sL -o /tmp/fz/disp.zip \
  "https://gwfh.mranftl.com/api/fonts/noto-sans-display?download=zip&subsets=latin,latin-ext,devanagari&variants=900,600&formats=ttf"
curl -sL -o /tmp/fz/sans.zip \
  "https://gwfh.mranftl.com/api/fonts/noto-sans?download=zip&subsets=latin,latin-ext,devanagari&variants=700&formats=ttf"
curl -sL -o /tmp/fz/serif.zip \
  "https://gwfh.mranftl.com/api/fonts/noto-serif?download=zip&subsets=latin,latin-ext,devanagari&variants=regular&formats=ttf"
for z in disp sans serif; do
  python3 -m zipfile -e /tmp/fz/$z.zip /tmp/fz/$z/
done
cp /tmp/fz/disp/*-900.ttf fonts/NotoSansDisplay-Black.ttf
cp /tmp/fz/disp/*-600.ttf fonts/NotoSansDisplay-SemiBold.ttf
cp /tmp/fz/sans/*-700.ttf fonts/NotoSans-Bold.ttf
cp /tmp/fz/serif/*-regular.ttf fonts/NotoSerif-Regular.ttf
ls -lh fonts

ls -lh .bin .bin/piper | head -30
.bin/ffmpeg -version | head -1
