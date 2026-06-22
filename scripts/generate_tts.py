import os
import sys
import json
import base64
from pathlib import Path

# Load dotenv if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def synthesize_elevenlabs(text, api_key, audio_path, timestamps_path):
    print("TTS: Using ElevenLabs API...")
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
    except ImportError:
        print("Error: elevenlabs SDK not installed. Run 'pip install elevenlabs'", file=sys.stderr)
        sys.exit(1)
        
    client = ElevenLabs(api_key=api_key)
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel or Bella
    model_id = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    
    response = client.text_to_speech.convert_with_timestamps(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        voice_settings=VoiceSettings(
            stability=float(os.environ.get("ELEVENLABS_STABILITY", "0.5")),
            similarity_boost=float(os.environ.get("ELEVENLABS_SIMILARITY", "0.75"))
        )
    )
    
    audio_bytes = b"".join(response.audio)
    audio_path.write_bytes(audio_bytes)
    
    # Process word-level timestamps
    words = []
    if response.normalized_alignment and response.normalized_alignment.characters:
        # Reconstruct words from character alignments
        current_word = ""
        word_start = None
        
        for char in response.normalized_alignment.characters:
            # Check for word boundary (space or punctuation start)
            if char.character.isspace():
                if current_word:
                    words.append({
                        "text": current_word,
                        "fromMs": int(word_start * 1000),
                        "toMs": int(char.start_time * 1000)
                    })
                    current_word = ""
                    word_start = None
            else:
                if word_start is None:
                    word_start = char.start_time
                current_word += char.character
                
        # Last word
        if current_word and word_start is not None:
            words.append({
                "text": current_word,
                "fromMs": int(word_start * 1000),
                "toMs": int(response.normalized_alignment.characters[-1].end_time * 1000)
            })
            
    timestamps_path.write_text(json.dumps({"words": words}, indent=2))
    print(f"✓ Saved ElevenLabs audio to {audio_path} and timestamps to {timestamps_path}")


def synthesize_omnivoice(text, api_url, audio_path, timestamps_path):
    print(f"TTS: Using OmniVoice Studio local API ({api_url})...")
    try:
        import httpx
    except ImportError:
        print("Error: httpx not installed. Run 'pip install httpx'", file=sys.stderr)
        sys.exit(1)
        
    try:
        resp = httpx.post(f"{api_url}/api/tts/generate", json={
            "text": text,
            "engine": os.environ.get("OMNIVOICE_ENGINE", "omnivoice"),
            "return_timestamps": True
        }, timeout=120)
        
        if resp.status_code != 200:
            print(f"Error: OmniVoice returned {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
            
        data = resp.json()
        audio_data = base64.b64decode(data["audio_base64"])
        audio_path.write_bytes(audio_data)
        
        # Format timestamps to standard {"words": [{"text": "...", "fromMs": X, "toMs": Y}]}
        raw_words = data.get("word_timestamps", [])
        words = []
        for rw in raw_words:
            words.append({
                "text": rw.get("word") or rw.get("text") or "",
                "fromMs": int(rw.get("start") or rw.get("fromMs") or 0),
                "toMs": int(rw.get("end") or rw.get("toMs") or 0)
            })
            
        timestamps_path.write_text(json.dumps({"words": words}, indent=2))
        print(f"✓ Saved OmniVoice audio to {audio_path} and timestamps to {timestamps_path}")
        
    except Exception as e:
        print(f"Error calling OmniVoice Studio: {e}", file=sys.stderr)
        print("Make sure OmniVoice Studio is running locally.", file=sys.stderr)
        sys.exit(1)


def main():
    narration_file = Path("video_script/narration.txt")
    if not narration_file.exists():
        print(f"Error: Narration file {narration_file} not found. Please create it first.", file=sys.stderr)
        sys.exit(1)
        
    text = narration_file.read_text(encoding="utf-8").strip()
    if not text:
        print("Error: Narration file is empty.", file=sys.stderr)
        sys.exit(1)
        
    # Prepare directories
    audio_dir = Path("audio")
    audio_dir.mkdir(exist_ok=True)
    
    audio_path = audio_dir / "narration.mp3"
    timestamps_path = audio_dir / "word_timestamps.json"
    
    # Check providers
    el_key = os.environ.get("ELEVENLABS_API_KEY")
    ov_url = os.environ.get("OMNIVOICE_API_URL", "http://localhost:49152") # default OVS port
    voice_provider = os.environ.get("VOICE_PROVIDER", "").strip().lower()
    
    # Run TTS
    if voice_provider == "omnivoice" or (not el_key and voice_provider != "elevenlabs"):
        synthesize_omnivoice(text, ov_url, audio_path, timestamps_path)
    elif el_key:
        synthesize_elevenlabs(text, el_key, audio_path, timestamps_path)
    else:
        print("No TTS provider keys or local API found. Skipping audio generation.", file=sys.stderr)
        print("To fix, set ELEVENLABS_API_KEY or OMNIVOICE_API_URL.", file=sys.stderr)
        # Create silent dummy files to prevent pipeline failure
        timestamps_path.write_text(json.dumps({"words": []}, indent=2))
        # Create 1s silent mp3 file if ffmpeg is available
        import subprocess
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
                "-t", "1", "-c:a", "libmp3lame", str(audio_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ Created dummy 1-second silent audio file.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
