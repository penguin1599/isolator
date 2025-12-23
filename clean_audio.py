import sys
import os
import subprocess
import argparse
import shutil
from pathlib import Path

def get_best_device():
    """Detect the best available device for GPU acceleration."""
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"[*] Using CUDA GPU: {device_name}")
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("[*] Using Apple Silicon GPU (MPS)")
            return "mps"
        else:
            print("[*] No GPU detected, using CPU (this will be slower)")
            return "cpu"
    except ImportError:
        print("[!] PyTorch not found, defaulting to CPU")
        return "cpu"

def run_command(command, description, use_shell=True):
    print(f"[*] {description}...")
    try:
        result = subprocess.run(command, check=True, shell=use_shell, 
                              capture_output=False, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error during {description}: {e}")
        print(f"[!] Command was: {command}")
        raise e

def check_dependencies():
    """Check if ffmpeg and demucs are installed."""
    if shutil.which("ffmpeg") is None:
        print("[!] ffmpeg is not installed or not in PATH.")
        exit(1)
    
    # Check for demucs
    try:
        subprocess.run([sys.executable, "-m", "demucs", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[!] demucs is not installed. Installing it now...")
        run_command(f"{sys.executable} -m pip install -U demucs", "Installing Demucs")

def clean_audio_pipeline(video_path, output_dir=None, force=False):
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"File not found: {video_path}")

    # Use provided output directory or default to video's directory
    if output_dir:
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = video_path.parent
    
    base_name = video_path.stem
    output_video = output_dir / f"{base_name}_clean.mp4"
    
    # Check if output already exists and is newer than input
    if output_video.exists() and not force:
        input_mtime = video_path.stat().st_mtime
        output_mtime = output_video.stat().st_mtime
        if output_mtime >= input_mtime:
            print(f"[→] Skipping {video_path.name} (already processed)")
            return False  # Indicates skipped
    
    # Detect best device for GPU acceleration
    device = get_best_device()
    
    temp_dir = output_dir / f"temp_{base_name}"
    
    # Define paths
    extracted_audio = temp_dir / "extracted_audio.wav"

    # Create temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        # Step 1: Extract Audio
        cmd_extract = f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le -ar 44100 -ac 2 "{extracted_audio}" -y'
        run_command(cmd_extract, "Extracting audio from video")

        # Step 2: Separate Audio using Demucs
        # -n htdemucs is the default high quality model
        # --two-stems=vocals implies we only want to split into 'vocals' and 'no_vocals' (everything else)
        # -d specifies the device (cuda, mps, or cpu)
        cmd_separate = f'"{sys.executable}" -m demucs -n htdemucs --two-stems=vocals -d {device} "{extracted_audio}" -o "{temp_dir}"'
        run_command(cmd_separate, f"Separating audio tracks (using {device.upper()})")

        # Demucs output structure: <out_dir>/htdemucs/<track_name>/vocals.wav
        # Since we passed a full path to demucs, the track name matches the filename 'extracted_audio'
        separated_vocals = temp_dir / "htdemucs" / "extracted_audio" / "vocals.wav"

        if not separated_vocals.exists():
             raise FileNotFoundError(f"Could not find separated vocals at: {separated_vocals}\n    Contents of temp dir: {list(temp_dir.rglob('*'))}")

        # Step 3: Remux Video with Clean Audio
        # -map 0:v:0 -> take video stream from input 0 (original video)
        # -map 1:a:0 -> take audio stream from input 1 (vocals.wav)
        # -c:v copy -> copy video stream without re-encoding
        # -c:a aac -> encode audio to AAC
        # -ignore_unknown -> skip unknown/unsupported streams like timecode
        cmd_remux = f'ffmpeg -i "{video_path}" -i "{separated_vocals}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -ignore_unknown "{output_video}" -y'
        run_command(cmd_remux, "Combining video with clean audio")

        print(f"[\u2713] Done! Clean video saved to: {output_video}")

    finally:
        # Cleanup
        if temp_dir.exists():
             print("[*] Cleaning up temporary files...")
             shutil.rmtree(temp_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strip background noise/music from a video file.")
    parser.add_argument("video_path", help="Path to the input video file or directory")
    parser.add_argument("-o", "--output", help="Output directory (default: same as input)")
    parser.add_argument("-f", "--force", action="store_true", help="Force reprocessing even if output exists")
    args = parser.parse_args()

    check_dependencies()
    
    input_path = Path(args.video_path).resolve()
    output_dir = args.output
    force = args.force
    
    if not input_path.exists():
        print(f"[!] Path not found: {input_path}")
        exit(1)

    video_extensions = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    
    if input_path.is_file():
        clean_audio_pipeline(input_path, output_dir, force)
    elif input_path.is_dir():
        print(f"[*] Processing all videos in directory: {input_path}")
        videos = [p for p in input_path.iterdir() if p.suffix.lower() in video_extensions]
        
        if not videos:
            print("[!] No video files found in the specified directory.")
        
        processed = 0
        skipped = 0
        failed = 0
        
        for i, video_file in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] Processing: {video_file.name}")
            try:
                result = clean_audio_pipeline(video_file, output_dir, force)
                if result is False:
                    skipped += 1
                else:
                    processed += 1
            except Exception as e:
                print(f"[!] Failed to process {video_file.name}: {e}")
                failed += 1
                continue
        
        # Print summary
        print(f"\n[✓] Summary: {processed} processed, {skipped} skipped, {failed} failed")
    else:
        print("[!] Input must be a valid file or directory.")
        exit(1)
