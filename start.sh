#!/usr/bin/env bash
cd "$(dirname "$0")"
export PATH="$PWD/.bin:$PATH"
export P2V_PIPER_BIN="$PWD/.bin/piper/piper"
export P2V_PIPER_MODEL="$PWD/.bin/hi_IN-rohan-medium.onnx"
export P2V_PIPER_MODEL_EN="$PWD/.bin/en_US-amy-medium.onnx"
exec python3 server.py
