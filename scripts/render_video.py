import os
import sys
import subprocess
import json
from pathlib import Path

# Load dotenv if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None

def get_audio_duration(audio_path):
    if MP3 is not None:
        try:
            return float(MP3(audio_path).info.length)
        except Exception:
            pass
            
    # Fallback to FFmpeg ffprobe
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not get exact audio duration: {e}. Defaulting to 15 seconds.", file=sys.stderr)
        return 15.0

def main():
    html_file = Path("video/composition.html")
    if not html_file.exists():
        print(f"Error: HTML composition file not found at {html_file}", file=sys.stderr)
        sys.exit(1)
        
    audio_path = Path("audio/narration.mp3")
    if not audio_path.exists():
        print("Warning: audio/narration.mp3 not found. Rendering silent video.", file=sys.stderr)
        audio_duration = 15.0
        has_audio = False
    else:
        audio_duration = get_audio_duration(audio_path)
        has_audio = True
        
    # Parameters
    fps = int(os.environ.get("RENDER_FPS", "30"))
    width = int(os.environ.get("RENDER_WIDTH", "1920"))
    height = int(os.environ.get("RENDER_HEIGHT", "1080"))
    output_path = Path(os.environ.get("RENDER_OUTPUT", "promo_output.mp4"))
    
    # Pad duration slightly to ensure last slide is fully shown
    total_seconds = audio_duration + 1.0 
    total_frames = int(total_seconds * fps)
    
    print(f"Rendering: {width}x{height} @ {fps}fps")
    print(f"Audio Duration: {audio_duration:.2f}s | Target Video Duration: {total_seconds:.2f}s ({total_frames} frames)")
    
    # Import Playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed. Run 'pip install playwright'", file=sys.stderr)
        sys.exit(1)
        
    # Construct FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-r", str(fps),
        "-vcodec", "png",
        "-i", "-", # Stdin pipe
    ]
    
    if has_audio:
        ffmpeg_cmd.extend([
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest", # End when shortest input ends (usually audio)
        ])
    else:
        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
        ])
        
    ffmpeg_cmd.append(str(output_path))
    
    print(f"Launching FFmpeg: {' '.join(ffmpeg_cmd)}")
    try:
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: FFmpeg is not installed or not on system PATH.", file=sys.stderr)
        print("Please run: winget install Gyan.FFmpeg (Windows) or brew install ffmpeg (Mac)", file=sys.stderr)
        sys.exit(1)
        
    abs_html_path = html_file.resolve().as_uri()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
        )
        page = context.new_page()
        
        print(f"Loading {abs_html_path} in Chromium...")
        page.goto(abs_html_path)
        page.wait_for_load_state("networkidle")
        
        # Check if GSAP is available in page
        has_gsap = page.evaluate("typeof gsap !== 'undefined'")
        if not has_gsap:
            print("Warning: GSAP is not found on the page. Animations might not seek frame-by-frame.", file=sys.stderr)
            
        print("Rendering frames...")
        for frame in range(total_frames):
            time_s = frame / fps
            
            # Seek GSAP timeline to the exact frame timestamp
            if has_gsap:
                page.evaluate(f"gsap.globalTimeline.seek({time_s})")
            
            # Take screenshot bytes
            screenshot_bytes = page.screenshot(type="png")
            
            # Pipe to FFmpeg
            try:
                ffmpeg_proc.stdin.write(screenshot_bytes)
            except OSError:
                print("Error: FFmpeg pipe closed prematurely.", file=sys.stderr)
                break
                
            if frame % 30 == 0:
                print(f"  Progress: {frame}/{total_frames} frames ({(frame/total_frames)*100:.1f}%)")
                
        # Close pipe and wait for FFmpeg to finish encoding
        ffmpeg_proc.stdin.close()
        ffmpeg_proc.wait()
        browser.close()
        
    if ffmpeg_proc.returncode == 0:
        print(f"🎬 Done! Final video saved to {output_path.resolve()}")
    else:
        print(f"Error: FFmpeg render failed with return code {ffmpeg_proc.returncode}", file=sys.stderr)

if __name__ == "__main__":
    main()
