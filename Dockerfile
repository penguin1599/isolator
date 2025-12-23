FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Set working directory
WORKDIR /app

# Install libsndfile for soundfile audio backend
RUN apt-get update && apt-get install -y libsndfile1 && rm -rf /var/lib/apt/lists/*

# Install PyTorch stable (for RTX 30xx/40xx and older) and Demucs
# noisereduce provides additional noise reduction for cleaner speech
RUN pip install --no-cache-dir \
    torch torchaudio --index-url https://download.pytorch.org/whl/cu121 \
    && pip install --no-cache-dir scipy soundfile demucs noisereduce

# Copy application code
COPY clean_audio.py .

# Set entrypoint
ENTRYPOINT ["python", "clean_audio.py"]
