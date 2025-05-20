# syntax=docker/dockerfile:1
FROM --platform=linux/arm64 python:3.9-slim-buster

# Unbuffered stdout/stderr, headless Qt
ENV PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=offscreen \
    QT_XCB_NATIVE_PAINTING=1

# Install only the minimal XCB libraries Qt needs (no libgl)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libxcb1 \
      libxcb-keysyms1 \
      libxcb-image0 \
      libxcb-render-util0 \
      libxcb-icccm4 \
      libxcb-xinerama0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY src .

# Run your entrypoint
CMD ["python", "render_app.py"]
