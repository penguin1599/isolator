import sys
import os
import subprocess
import argparse
import shutil
from pathlib import Path

def run_command(command, description):
    print(f"[*] {description}...")
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error during {description}: {e}")
        exit(1)

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

def clean_audio_pipeline(video_path):
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        print(f"[!] File not found: {video_path}")
        exit(1)

    project_dir = video_path.parent
    base_name = video_path.stem
    temp_dir = project_dir / f"temp_{base_name}"
    
    # Define paths
    extracted_audio = temp_dir / "extracted_audio.wav"
    output_video = project_dir / f"{base_name}_clean.mp4"

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
        cmd_separate = f'"{sys.executable}" -m demucs -n htdemucs --two-stems=vocals "{extracted_audio}" -o "{temp_dir}"'
        run_command(cmd_separate, "Separating audio tracks")

        # Demucs output structure: <out_dir>/htdemucs/<track_name>/vocals.wav
        # Since we passed a full path to demucs, the track name matches the filename 'extracted_audio'
        separated_vocals = temp_dir / "htdemucs" / "extracted_audio" / "vocals.wav"

        if not separated_vocals.exists():
             print(f"[!] Could not find separated vocals at: {separated_vocals}")
             print(f"    Contents of temp dir: {list(temp_dir.rglob('*'))}")
             exit(1)

        # Step 3: Remux Video with Clean Audio
        # -map 0:v:0 -> take video stream from input 0 (original video)
        # -map 1:a:0 -> take audio stream from input 1 (vocals.wav)
        # -c:v copy -> copy video stream without re-encoding
        # -c:a aac -> encode audio to AAC
        cmd_remux = f'ffmpeg -i "{video_path}" -i "{separated_vocals}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k "{output_video}" -y'
        run_command(cmd_remux, "Combining video with clean audio")

        print(f"[\u2713] Done! Clean video saved to: {output_video}")

    finally:
        # Cleanup
        if temp_dir.exists():
             print("[*] Cleaning up temporary files...")
             shutil.rmtree(temp_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strip background noise/music from a video file.")
    parser.add_argument("video_path", help="Path to the input video file")
    args = parser.parse_args()

    check_dependencies()
    clean_audio_pipeline(args.video_path)
