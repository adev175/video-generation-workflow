---
name: html-gsap-video-best-practices
description: Best practices for generating programmatic videos using HTML + GSAP and rendering with Playwright + FFmpeg
metadata:
  tags: gsap, html, rendering, playwright, ffmpeg, animation, composition
---

## When to Use

Use this skill whenever you are designing or writing code for an HTML-based video composition using GSAP (GreenSock Animation Platform) and rendering it using a headless browser (Playwright) + FFmpeg.

## Core Animation Rule (Seeks and Ticks)

Traditional CSS transitions, CSS `@keyframes` animations, and requestAnimationFrame loops are **FORBIDDEN** for frame-accurate renders. They execute in wall-clock time, which drops frames or causes audio sync issues when Playwright takes screenshots.

1.  **Always use GSAP** (`gsap.timeline()` or `gsap.to()`) to orchestrate animations.
2.  All animations must be added to a single global timeline or registered properly so they can be controlled via `gsap.globalTimeline.seek()`.
3.  The renderer script (`render_video.py`) will automatically step through the video time (e.g., `seek(frame / fps)`) and take screenshots.

### Good Animation Pattern

```html
<h1 id="title" style="opacity: 0;">Hello World</h1>
<script>
  const tl = gsap.timeline({ paused: true }); // Pause by default, let renderer drive
  tl.to("#title", { opacity: 1, duration: 1.0, ease: "power2.out" });
  
  // Renderer seeks:
  // gsap.globalTimeline.seek(timestamp_seconds)
</script>
```

## Screen Sizing & Styling

1.  **Fixed Viewport**: Always design for a fixed viewport size, usually **1920x1080** (Full HD) or **1080x1920** (TikTok/Shorts).
2.  **CSS Reset**: Apply absolute styling and set body width/height explicitly:
    ```css
    body {
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      margin: 0;
      padding: 0;
    }
    ```
3.  **Aesthetics**: Use modern Google Fonts (e.g., *Outfit*, *Inter*, *Cabinet Grotesk*), dark themes (`#0f0f23`), subtle glowing gradients, glassmorphism borders (`border: 2px solid rgba(255,255,255,0.1)`), and deep shadows to make it feel premium.

## Subtitle Synchronization

1.  Always read word-level timestamps from `audio/word_timestamps.json`.
2.  Add a ticker callback to GSAP to update the subtitle HTML during playback/rendering:
    ```javascript
    gsap.ticker.add(() => {
      const timeMs = gsap.globalTimeline.time() * 1000;
      // Filter words based on timeMs and highlight the active word
    });
    ```
3.  Keep subtitles near the bottom center, styled with high contrast (text shadow, font weight 600+) and a glowing highlight color (like `#00e5ff` or `#39E508`).
