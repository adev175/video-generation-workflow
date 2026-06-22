# Programmatic Video Generation Workflow Kit (AI-Ready & Standalone)

This kit provides a structured, drop-in workflow and knowledge base for automating video creation using **Remotion** (React-based video editing) or **HTML + GSAP** (GreenSock Animation Platform) rendered with Playwright & FFmpeg. 

**This kit is 100% standalone and does NOT require the any PLugin CLI or any complex orchestration setup.** It works natively with any terminal and coding agent (such as Claude Code or the Gemini CLI).

---

## 📂 Directory Structure

```text
video-generation-workflow-kit/
├── README.md               # This integration guide
├── templates/
│   └── composition.html    # Boilerplate HTML/GSAP composition with synced word highlights
├── skills/                 # Agent instructions (copy to .agents/skills/ or .claude/skills/)
│   ├── html-gsap-video-best-practices/ # Rules for HTML + GSAP rendering
│   ├── remotion-best-practices/        # Rules for React + Remotion rendering
│   └── visual-diagrams/                # Design rules for tech stacks and flowcharts
└── scripts/                # Standalone Python scripts for pipeline execution
    ├── take_screenshots.py # Playwright screenshot capture tool
    ├── generate_tts.py     # TTS generator (supports ElevenLabs & Local OmniVoice API)
    └── render_video.py     # Playwright frame-by-frame HTML/GSAP to MP4 renderer
```

---

## ⚙️ Prerequisites & Setup

Ensure the following tools are installed on your machine:

1.  **FFmpeg** (Required for video rendering & local TTS):
    *   **Windows**: `winget install Gyan.FFmpeg`
    *   **macOS**: `brew install ffmpeg`
2.  **Node.js & Python**:
    *   Node.js v20+
    *   Python 3.11+
3.  **Python Script Dependencies**:
    *   Install necessary libraries:
        ```bash
        pip install playwright mutagen httpx python-dotenv
        playwright install chromium
        ```

### Environment Variables
Create a `.env` file in your target project root:
```env
# Target URL for capturing screenshots
APP_URL=http://localhost:8000

# TTS Settings (Configure ONE of the options below)

# OPTION A: ElevenLabs API (Paid/Free, cloud)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# OPTION B: Local OmniVoice Studio (100% free, runs locally)
# VOICE_PROVIDER=omnivoice
# OMNIVOICE_API_URL=http://localhost:49152
```

---

## 🚀 The 5-Phase Production Pipeline

When you want your coding agent (e.g. Claude Code) to build a promo video for your app, instruct it to execute these 5 phases:

### Phase 1: Research & Capture
1.  Read the app's `README.md` or files to understand its main features, name, and tone.
2.  Make sure the app is running (e.g., at `http://localhost:8000`).
3.  Run `python scripts/take_screenshots.py` to capture screenshots of the active pages. They will be saved to `screenshots/`.

### Phase 2: Script & Narration Planning
1.  Plan a 45–60s narration script. Write it directly to `video_script/narration.txt`.
2.  Plan the slide-by-slide scenes (e.g., Intro → App screenshot showing features → CTA).

### Phase 3: Text-to-Speech & Alignment
1.  Run `python scripts/generate_tts.py`.
2.  This generates `audio/narration.mp3` and `audio/word_timestamps.json` (which aligns each spoken word with millisecond timings for precise caption highlights).

### Phase 4: Composition
Depending on your preference, choose one of the two rendering engines:

#### Engine A: HTML + GSAP (Simple & Zero-Scaffold)
1.  Copy `templates/composition.html` into `video/composition.html` in your project.
2.  Modify the HTML/CSS structure to reflect the screenshots, app name, and scenes.
3.  Adjust the slide timings in the JavaScript GSAP timeline to match the duration of the audio.
4.  *Rule*: Do **not** use CSS animations or transitions. Drive everything via the GSAP timeline so Playwright can seek frames accurately.

#### Engine B: React + Remotion (Powerful Component Engine)
1.  If you prefer React, scaffold a Remotion project using `npx create-video@latest --yes --blank --no-tailwind video-project`.
2.  Copy `skills/remotion-best-practices/` into your agent settings.
3.  Code your video components in React, using `useCurrentFrame()` and `interpolate()` to drive all visual transitions.

### Phase 5: Rendering
*   If using **HTML + GSAP**: Run `python scripts/render_video.py`. Playwright will launch Chromium, step through the timeline frame-by-frame, capture images, and feed them into FFmpeg to write `promo_output.mp4`.
*   If using **Remotion**: Run `npx remotion render` inside the React project directory.

---

## 🎨 Visual Quality & Design Rules

*   **Atmosphere**: Use deep, dark backgrounds (`#0c0b1e`), vibrant gradients, and high-contrast text.
*   **Screenshots**: Wrap screenshots in `border-radius: 12px` and deep box-shadows so they pop against the background.
*   **Subtitles**: Style subtitles with a bold, readable font (e.g. `Outfit` or `Inter`), and highlight the current word being spoken with a distinct color (e.g., `#00e5ff` or `#39E508`) using the word alignment json.
