---
name: ffmpeg
description: Edit videos, extract audio, create GIFs, add subtitles, compress, and manipulate media files using ffmpeg. Use whenever the user mentions video editing, audio extraction, format conversion, GIF creation, compression, watermarks, subtitles, thumbnails, video speed, stabilization, or any media file manipulation. Trigger on "edit video", "cut video", "trim", "merge videos", "extract audio", "make a GIF", "add subtitles", "compress", "resize video", "convert to mp4", "watermark", "slow motion", "timelapse", "thumbnail", "stabilize", "fade in/out", "replace audio", "change volume", or similar.
---

# FFmpeg Video Editor

Edit video, audio, and images from the terminal using ffmpeg and the `fftools.py` helper script.

## CLI Tool

All operations go through the helper script. Find it relative to where you cloned the repo, or at:

```bash
SCRIPT="~/.claude/skills/ffmpeg/scripts/fftools.py"
```

All output is JSON.

## Commands Reference

```bash
# INFO — Get file details (duration, resolution, codecs, size)
python3 $SCRIPT info input.mp4

# CUT — Extract a segment
python3 $SCRIPT cut input.mp4 output.mp4 --start 00:01:30 --end 00:02:45
python3 $SCRIPT cut input.mp4 output.mp4 --start 00:01:30 --duration 30

# MERGE — Concatenate multiple videos
python3 $SCRIPT merge video1.mp4 video2.mp4 video3.mp4 -o merged.mp4
python3 $SCRIPT merge video1.mp4 video2.mp4 -o merged.mp4 --reencode  # different codecs

# EXTRACT AUDIO — Rip audio track
python3 $SCRIPT extract-audio input.mp4 output.mp3
python3 $SCRIPT extract-audio input.mp4 output.opus --bitrate 128k

# SUBTITLES — Burn subtitles into video
python3 $SCRIPT subtitles input.mp4 output.mp4 --srt subs.srt

# RESIZE — Change resolution
python3 $SCRIPT resize input.mp4 output.mp4 --width 1280 --height 720
python3 $SCRIPT resize input.mp4 output.mp4 --width 1920 --height -1  # auto height

# GIF — Video to animated GIF (two-pass, high quality)
python3 $SCRIPT gif input.mp4 output.gif --fps 15 --width 480
python3 $SCRIPT gif input.mp4 output.gif --start 00:00:05 --duration 3

# THUMBNAIL — Extract single frame
python3 $SCRIPT thumbnail input.mp4 thumb.jpg --time 00:00:30

# THUMBNAILS — Extract N evenly-spaced frames
python3 $SCRIPT thumbnails input.mp4 --count 10 --output-dir ./thumbs/

# COMPRESS — Reduce file size
python3 $SCRIPT compress input.mp4 output.mp4 --crf 28 --preset medium
python3 $SCRIPT compress input.mp4 small.mp4 --crf 32 --preset fast  # aggressive

# SPEED — Change playback speed
python3 $SCRIPT speed input.mp4 fast.mp4 --factor 2.0    # 2x faster
python3 $SCRIPT speed input.mp4 slow.mp4 --factor 0.5    # half speed (slow-mo)

# WATERMARK — Add image overlay
python3 $SCRIPT watermark input.mp4 output.mp4 --watermark logo.png --position bottom-right

# TEXT — Burn text overlay
python3 $SCRIPT text input.mp4 output.mp4 --text "Chapter 1" --position center --size 72 --border
python3 $SCRIPT text input.mp4 output.mp4 --text "Sale!" --position top-left --start 5 --end 15

# CONVERT — Change format
python3 $SCRIPT convert input.avi output.mp4
python3 $SCRIPT convert input.mp4 output.webm --video-codec libvpx-vp9

# FRAMES — Extract frames as images
python3 $SCRIPT frames input.mp4 --output-dir ./frames/
python3 $SCRIPT frames input.mp4 --output-dir ./frames/ --every 30  # every 30th frame

# AUDIO REPLACE — Swap audio track
python3 $SCRIPT audio-replace input.mp4 output.mp4 --audio music.mp3

# VOLUME — Adjust audio level
python3 $SCRIPT volume input.mp4 output.mp4 --level 2.0      # double volume
python3 $SCRIPT volume input.mp4 output.mp4 --level 0.5      # halve volume
python3 $SCRIPT volume input.mp4 output.mp4 --level 10dB     # boost 10dB

# FADE — Add fade in/out effects
python3 $SCRIPT fade input.mp4 output.mp4 --fade-in 2 --fade-out 3

# STABILIZE — Fix shaky video (requires vidstab filter)
python3 $SCRIPT stabilize input.mp4 output.mp4 --shakiness 7 --smoothing 15
```

## Standard Workflow

### Step 1 — Analyze the input
Always start by getting file info:
```bash
python3 $SCRIPT info input.mp4
```
This tells you duration, resolution, codecs, file size. Use this to make smart decisions about output settings.

### Step 2 — Perform the operation
Use the appropriate command. For complex edits, chain multiple operations — use the output of one as input to the next.

### Step 3 — Verify the result
After any operation, probe the output to confirm it worked:
```bash
python3 $SCRIPT info output.mp4
```

### Step 4 — Show the result
Use the Read tool to display images (thumbnails, frames). For videos, tell the user the output path and file size.

## Raw ffmpeg — For advanced operations

When the helper script doesn't cover your use case, use ffmpeg directly:

```bash
# Picture-in-picture
ffmpeg -y -i main.mp4 -i overlay.mp4 \
  -filter_complex "[1:v]scale=320:-1[pip];[0:v][pip]overlay=W-w-10:H-h-10" \
  -c:v libx264 -c:a copy output.mp4

# Side-by-side comparison
ffmpeg -y -i left.mp4 -i right.mp4 \
  -filter_complex "[0:v]pad=iw*2:ih[bg];[bg][1:v]overlay=W/2:0" \
  -c:v libx264 output.mp4

# Grid/mosaic (2x2)
ffmpeg -y -i a.mp4 -i b.mp4 -i c.mp4 -i d.mp4 \
  -filter_complex "[0:v]scale=640:360[v0];[1:v]scale=640:360[v1];
    [2:v]scale=640:360[v2];[3:v]scale=640:360[v3];
    [v0][v1]hstack[top];[v2][v3]hstack[bot];[top][bot]vstack" \
  -c:v libx264 grid.mp4

# Reverse video
ffmpeg -y -i input.mp4 -vf reverse -af areverse reversed.mp4

# Extract specific audio channel
ffmpeg -y -i input.mp4 -af "pan=mono|c0=FL" left_channel.wav

# Noise reduction
ffmpeg -y -i input.mp4 -af "afftdn=nf=-25" denoised.mp4

# Color correction (brightness, contrast, saturation)
ffmpeg -y -i input.mp4 -vf "eq=brightness=0.1:contrast=1.2:saturation=1.3" corrected.mp4

# Chroma key (green screen removal)
ffmpeg -y -i greenscreen.mp4 -i background.mp4 \
  -filter_complex "[0:v]chromakey=0x00FF00:0.3:0.1[fg];[1:v][fg]overlay" \
  -c:v libx264 composited.mp4

# Timelapse from image sequence
ffmpeg -y -framerate 30 -i frame_%04d.jpg -c:v libx264 -pix_fmt yuv420p timelapse.mp4

# Video from single image + audio
ffmpeg -y -loop 1 -i cover.jpg -i audio.mp3 -c:v libx264 -tune stillimage \
  -c:a aac -shortest output.mp4

# Crossfade between two videos (1 second)
ffmpeg -y -i first.mp4 -i second.mp4 \
  -filter_complex "xfade=transition=fade:duration=1:offset=FIRST_DURATION_MINUS_1" \
  -c:v libx264 crossfade.mp4
```

## CRF Quality Guide

| CRF | Quality | Use case |
|-----|---------|----------|
| 18 | Visually lossless | Archival, professional editing |
| 23 | High quality | Default ffmpeg, good for most uses |
| 28 | Good quality | Recommended for sharing, smaller files |
| 32 | Acceptable | Social media, aggressive compression |
| 38+ | Low quality | Previews, thumbnails |

Lower CRF = larger file, better quality. Each +6 roughly halves the file size.

## Format Quick Reference

| Container | Video codec | Audio codec | Use case |
|-----------|-----------|-------------|----------|
| `.mp4` | H.264 (libx264) | AAC | Universal compatibility |
| `.webm` | VP9 (libvpx-vp9) | Opus | Web, smaller files |
| `.mkv` | H.265 (libx265) | Opus | Maximum compression |
| `.mov` | ProRes | PCM | Professional editing |
| `.gif` | — | — | Animations, no audio |

## Error Handling

- **"No such file"** — Check the input path, use absolute paths
- **"Unknown encoder"** — Codec not compiled in. Check `ffmpeg -encoders`
- **"Permission denied"** — Output path not writable
- **"Avi header too large"** — Corrupted input, try `-fflags +genpts` before input
- **Timeout** — Video is very long. Increase timeout or use `--preset ultrafast`
- **Out of memory** — Reduce resolution first, then process
