import os
import shutil
import subprocess
import imageio_ffmpeg

def get_ffmpeg_binary() -> str:
    """Returns system ffmpeg if available, otherwise bundled imageio-ffmpeg binary."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def extract_and_compress_audio(input_path: str, output_path: str = None) -> str:
    """
    Takes any video or audio file (MP4, MKV, MOV, AVI, 3GP, AMR, M4A, OPUS, OGG, WAV, etc.)
    and extracts a clean, optimized voice audio file (16kHz mono MP3, 48kbps).
    A 2-hour video drops from 2-4GB to ~42MB, preserving crystal-clear voice fidelity.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}_voice_optimized.mp3"

    ffmpeg = get_ffmpeg_binary()

    cmd = [
        ffmpeg,
        "-y",               # Overwrite output without asking
        "-i", input_path,   # Input file
        "-vn",              # Disable video stream
        "-ac", "1",         # Convert to mono channel
        "-ar", "16000",     # 16000 Hz sample rate (optimal for speech AI)
        "-acodec", "libmp3lame",
        "-b:a", "48k",      # 48k bitrate
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed:\n{result.stderr}")

    return output_path

def get_file_size_mb(path: str) -> float:
    """Returns file size in megabytes."""
    if os.path.exists(path):
        return round(os.path.getsize(path) / (1024 * 1024), 2)
    return 0.0
