#!/usr/bin/env python3
"""
Video Transcoding Script
Recursively finds video files in a folder and transcodes them to H.264 MP4 format.
"""

import os
import subprocess
import sys
from pathlib import Path

# Common video file extensions
VIDEO_EXTENSIONS = {
    '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
    '.mpg', '.mpeg', '.3gp', '.asf', '.rm', '.rmvb', '.vob',
    '.ts', '.mts', '.m2ts', '.divx', '.xvid', '.ogv'
}

def is_video_file(file_path):
    """Check if file is a video file based on extension."""
    return file_path.suffix.lower() in VIDEO_EXTENSIONS

def is_already_h264_mp4(file_path):
    """Check if file is already H.264 MP4 to avoid unnecessary transcoding."""
    if file_path.suffix.lower() != '.mp4':
        return False
    
    try:
        # Use ffprobe to check codec
        cmd = [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name', '-of', 'csv=p=0',
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip().lower() == 'h264'
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False

def transcode_video(input_path, output_path):
    """Transcode video to H.264 MP4 format."""
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-c:v', 'libx264',           # H.264 video codec
        '-crf', '23',                # Constant Rate Factor (normal quality)
        '-preset', 'medium',         # Encoding speed vs compression efficiency
        '-c:a', 'aac',               # AAC audio codec
        '-b:a', '128k',              # Audio bitrate
        '-movflags', '+faststart',   # Optimize for web streaming
        '-y',                        # Overwrite output file if exists
        str(output_path)
    ]
    
    print(f"Transcoding: {input_path.name}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            print(f"✓ Successfully transcoded: {output_path}")
            return True
        else:
            print(f"✗ Error transcoding {input_path.name}:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout transcoding {input_path.name}")
        return False
    except Exception as e:
        print(f"✗ Exception transcoding {input_path.name}: {e}")
        return False

def find_and_transcode_videos(folder_path, output_folder=None, replace_original=False):
    """
    Find and transcode all videos in folder and subfolders.
    
    Args:
        folder_path: Path to search for videos
        output_folder: Optional separate output folder
        replace_original: If True, replace original files
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    if not folder.is_dir():
        print(f"Error: '{folder_path}' is not a directory.")
        return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        return
    
    print(f"Scanning for videos in: {folder}")
    print("-" * 50)
    
    video_files = []
    for file_path in folder.rglob('*'):
        if file_path.is_file() and is_video_file(file_path):
            if not is_already_h264_mp4(file_path):
                video_files.append(file_path)
            else:
                print(f"Skipping (already H.264 MP4): {file_path.name}")
    
    if not video_files:
        print("No videos found that need transcoding.")
        return
    
    print(f"\nFound {len(video_files)} video(s) to transcode:")
    for i, video in enumerate(video_files, 1):
        print(f"{i}. {video}")
    
    print("\n" + "="*50)
    
    success_count = 0
    for i, input_path in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}]")
        
        # Determine output path
        if output_folder:
            output_dir = Path(output_folder)
            output_dir.mkdir(parents=True, exist_ok=True)
            # Maintain relative folder structure
            rel_path = input_path.relative_to(folder)
            output_path = output_dir / rel_path.with_suffix('.mp4')
            output_path.parent.mkdir(parents=True, exist_ok=True)
        elif replace_original:
            output_path = input_path.with_suffix('.mp4')
        else:
            # Add suffix to avoid overwriting
            output_path = input_path.with_name(f"{input_path.stem}_h264.mp4")
        
        if transcode_video(input_path, output_path):
            success_count += 1
            
            # If replacing original and transcoding successful, remove original
            if replace_original and input_path != output_path:
                try:
                    input_path.unlink()
                    print(f"Removed original: {input_path.name}")
                except Exception as e:
                    print(f"Warning: Could not remove original file: {e}")
    
    print("\n" + "="*50)
    print(f"Transcoding complete: {success_count}/{len(video_files)} successful")

def main():
    """Main function with command line argument parsing."""
    if len(sys.argv) < 2:
        print("Usage: python transcode_videos.py <folder_path> [options]")
        print("\nOptions:")
        print("  --output-folder <path>  : Save transcoded files to separate folder")
        print("  --replace-original      : Replace original files (use with caution!)")
        print("\nExample:")
        print("  python transcode_videos.py /path/to/videos")
        print("  python transcode_videos.py /path/to/videos --output-folder /path/to/output")
        return
    
    folder_path = sys.argv[1]
    output_folder = None
    replace_original = False
    
    # Parse additional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--output-folder' and i + 1 < len(sys.argv):
            output_folder = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--replace-original':
            replace_original = True
            i += 1
        else:
            print(f"Unknown argument: {sys.argv[i]}")
            return
    
    if replace_original and output_folder:
        print("Error: Cannot use --replace-original with --output-folder")
        return
    
    if replace_original:
        response = input("Warning: This will replace original files. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    find_and_transcode_videos(folder_path, output_folder, replace_original)

if __name__ == "__main__":
    main()
