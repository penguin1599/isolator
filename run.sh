#!/bin/bash
# Audio Isolator - Cross-platform run script
# Works on Linux (with NVIDIA GPU) and macOS (Apple Silicon native)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)

echo -e "${GREEN}[*] Audio Isolator${NC}"
echo -e "[*] Platform: $PLATFORM ($ARCH)"

# Check if running on macOS
if [[ "$PLATFORM" == "Darwin" ]]; then
    echo -e "${YELLOW}[*] macOS detected - running natively (Docker doesn't support MPS)${NC}"
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[!] Python 3 not found. Please install Python 3.10+${NC}"
        exit 1
    fi
    
    # Check for ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${YELLOW}[!] ffmpeg not found. Installing via Homebrew...${NC}"
        brew install ffmpeg
    fi
    
    # Check for virtual environment
    if [[ ! -d "venv" ]]; then
        echo -e "[*] Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies if needed
    if ! python -c "import demucs" 2>/dev/null; then
        echo -e "[*] Installing dependencies..."
        pip install --upgrade pip
        pip install torch torchaudio demucs
    fi
    
    # Create directories
    mkdir -p input output
    
    # Run the script
    if [[ -z "$1" ]]; then
        echo -e "[*] Processing all files in input/ directory..."
        python clean_audio.py input/ -o output/
    else
        python clean_audio.py "input/$1" -o output/
    fi
    
    deactivate

# Linux with Docker
elif [[ "$PLATFORM" == "Linux" ]]; then
    echo -e "[*] Linux detected - using Docker with NVIDIA GPU"
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[!] Docker not found. Please install Docker.${NC}"
        exit 1
    fi
    
    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        echo -e "[*] Detected GPU: $GPU_NAME"
        
        # Select Dockerfile based on GPU (RTX 50-series needs nightly)
        if [[ "$GPU_NAME" == *"5090"* ]] || [[ "$GPU_NAME" == *"5080"* ]] || [[ "$GPU_NAME" == *"5070"* ]]; then
            echo -e "[*] Using Blackwell-optimized Dockerfile (CUDA 12.8 + PyTorch nightly)"
            DOCKERFILE="Dockerfile.5090"
            IMAGE_TAG="audio-cleaner:5090"
        else
            echo -e "[*] Using standard Dockerfile (CUDA 12.1 + PyTorch stable)"
            DOCKERFILE="Dockerfile"
            IMAGE_TAG="audio-cleaner:latest"
        fi
    else
        echo -e "${YELLOW}[!] No NVIDIA GPU detected, using CPU mode${NC}"
        DOCKERFILE="Dockerfile"
        IMAGE_TAG="audio-cleaner:latest"
    fi
    
    # Create directories
    mkdir -p input output models
    
    # Build the image
    docker build -t "$IMAGE_TAG" -f "$DOCKERFILE" .
    
    # Run with GPU access
    if [[ -z "$1" ]]; then
        echo -e "[*] Processing all files in input/ directory..."
        docker run --rm -it \
            --gpus all \
            -v "$(pwd)/input:/input" \
            -v "$(pwd)/output:/output" \
            -v "$(pwd)/models:/root/.cache/torch/hub/checkpoints" \
            "$IMAGE_TAG" "/input" -o "/output"
    else
        docker run --rm -it \
            --gpus all \
            -v "$(pwd)/input:/input" \
            -v "$(pwd)/output:/output" \
            -v "$(pwd)/models:/root/.cache/torch/hub/checkpoints" \
            "$IMAGE_TAG" "/input/$1" -o "/output"
    fi

else
    echo -e "${RED}[!] Unsupported platform: $PLATFORM${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Done!${NC}"
