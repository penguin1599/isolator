#!/bin/bash
# Build and run the audio cleaner with GPU support

# Build the image (if not already built)
docker build -t audio-cleaner .

# Run with GPU access and mount current directory
# Usage: ./run.sh <video_file_or_directory>
docker run --rm -it \
    --gpus all \
    -v "$(pwd):/data" \
    audio-cleaner "/data/$1"
