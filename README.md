# Audio Isolator

A video pipeline that removes background noise and music, retaining only clean speech using AI-powered source separation (Demucs).

## Features

- 🎯 **AI-Powered**: Uses Facebook's Demucs neural network for studio-quality vocal isolation
- ⚡ **GPU Accelerated**: CUDA (NVIDIA) and MPS (Apple Silicon) support
- 🐳 **Dockerized**: No dependency hell on Windows/Linux
- 📁 **Batch Processing**: Drop multiple videos, process all at once

## Quick Start

### Windows (Docker + NVIDIA GPU)

```batch
# Drop videos in input/ folder, then:
run.bat
```

### Linux (Docker + NVIDIA GPU)

```bash
chmod +x run.sh
./run.sh
```

### macOS (Apple Silicon - Native)

```bash
chmod +x run.sh
./run.sh
```

> **Note**: Docker on macOS cannot access MPS (Metal). The script automatically runs natively on Mac.

## Supported Hardware

| Platform | GPU | Method | Performance |
|----------|-----|--------|-------------|
| Windows | RTX 50-series (5090, 5080, 5070) | Docker + CUDA 12.8 nightly | ⚡ Fastest |
| Windows | RTX 40/30/20 series | Docker + CUDA 12.1 stable | ⚡ Fast |
| Windows | GTX 10-series, older | Docker + CUDA 12.1 stable | ⚡ Fast |
| Linux | Any NVIDIA GPU | Docker + CUDA | ⚡ Fast |
| macOS | Apple Silicon (M1-M4) | Native + MPS | ⚡ Fast |
| Any | CPU only | Docker or Native | 🐢 Slow |

## Directory Structure

```
isolator/
├── input/          # Drop your videos here
├── output/         # Cleaned videos appear here
├── models/         # Cached AI models (auto-downloaded)
├── run.bat         # Windows launcher
├── run.sh          # Linux/macOS launcher
├── clean_audio.py  # Main processing script
├── Dockerfile      # For RTX 40/30/20 and older
└── Dockerfile.5090 # For RTX 50-series (Blackwell)
```

## Usage

### Process all videos in input folder:
```bash
# Windows
run.bat

# Linux/macOS
./run.sh
```

### Process a specific file:
```bash
# Windows
run.bat my_video.mp4

# Linux/macOS
./run.sh my_video.mp4
```

### Direct Python usage (no Docker):
```bash
# Install dependencies
pip install torch torchaudio demucs ffmpeg-python

# Run
python clean_audio.py path/to/video.mp4 -o output/
```

## How It Works

1. **Extract Audio**: FFmpeg extracts audio from video
2. **AI Separation**: Demucs separates vocals from music/noise using GPU
3. **Remux**: FFmpeg combines original video with clean audio

## Requirements

### Windows/Linux (Docker)
- Docker Desktop
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit (Linux)

### macOS (Native)
- Python 3.10+
- Homebrew (for FFmpeg)
- Apple Silicon (M1/M2/M3/M4) recommended

## Troubleshooting

### "Model downloading every run"
Models are cached in `models/` directory. Ensure it exists and is mounted correctly.

### "CUDA not available"
- Windows: Ensure Docker Desktop has WSL 2 backend with GPU support enabled
- Linux: Install NVIDIA Container Toolkit: `nvidia-ctk runtime configure`

### "RTX 5090 not working"
RTX 50-series (Blackwell) requires PyTorch nightly. The script auto-detects and uses `Dockerfile.5090`.

## License

MIT
