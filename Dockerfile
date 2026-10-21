FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl ca-certificates fonts-noto-core fonts-noto-extra \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pillow

WORKDIR /app
COPY . /app
RUN mkdir -p /app/outputs && chmod 777 /app/outputs

# Piper TTS binary + Hindi voice (free, local at runtime)
RUN curl -sL -o /tmp/piper.tar.gz \
      https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz \
    && tar xzf /tmp/piper.tar.gz -C /opt && rm /tmp/piper.tar.gz \
    && curl -sL -o /opt/hi_IN-rohan-medium.onnx \
      https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx \
    && curl -sL -o /opt/hi_IN-rohan-medium.onnx.json \
      https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx.json \
    && curl -sL -o /opt/en_US-amy-medium.onnx \
      https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx \
    && curl -sL -o /opt/en_US-amy-medium.onnx.json \
      https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json

ENV P2V_PIPER_BIN=/opt/piper/piper \
    P2V_PIPER_MODEL=/opt/hi_IN-rohan-medium.onnx \
    P2V_PIPER_MODEL_EN=/opt/en_US-amy-medium.onnx \
    PORT=7860

EXPOSE 7860
CMD ["python3", "server.py"]
