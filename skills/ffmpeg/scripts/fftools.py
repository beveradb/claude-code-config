#!/usr/bin/env python3
"""
fftools — High-level CLI wrapper around ffmpeg/ffprobe for common video operations.
All output is JSON for easy parsing. Zero dependencies beyond Python stdlib + ffmpeg.
"""
import argparse
import json
import os
import subprocess
import sys
import re
import tempfile
from pathlib import Path


def run_cmd(cmd, timeout=300, capture=True):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            cmd, capture_output=capture, text=True, timeout=timeout
        )
        return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}
    except FileNotFoundError:
        return {"returncode": -1, "stdout": "", "stderr": f"Command not found: {cmd[0]}"}


def probe(input_file):
    """Get detailed media info as JSON."""
    result = run_cmd([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        input_file
    ])
    if result["returncode"] != 0:
        return {"error": result["stderr"]}
    try:
        data = json.loads(result["stdout"])
        # Build a summary
        summary = {"file": input_file, "streams": [], "format": {}}
        fmt = data.get("format", {})
        summary["format"] = {
            "duration": float(fmt.get("duration", 0)),
            "duration_human": format_duration(float(fmt.get("duration", 0))),
            "size_bytes": int(fmt.get("size", 0)),
            "size_human": format_size(int(fmt.get("size", 0))),
            "bit_rate": int(fmt.get("bit_rate", 0)),
            "format_name": fmt.get("format_name", ""),
        }
        for s in data.get("streams", []):
            stream_info = {
                "type": s.get("codec_type"),
                "codec": s.get("codec_name"),
            }
            if s.get("codec_type") == "video":
                stream_info.update({
                    "width": s.get("width"),
                    "height": s.get("height"),
                    "fps": eval_fps(s.get("r_frame_rate", "0/1")),
                    "pix_fmt": s.get("pix_fmt"),
                })
            elif s.get("codec_type") == "audio":
                stream_info.update({
                    "sample_rate": s.get("sample_rate"),
                    "channels": s.get("channels"),
                    "channel_layout": s.get("channel_layout"),
                })
            elif s.get("codec_type") == "subtitle":
                stream_info.update({
                    "language": s.get("tags", {}).get("language", ""),
                })
            summary["streams"].append(stream_info)
        return summary
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return {"error": str(e), "raw": result["stdout"][:500]}


def eval_fps(rate_str):
    """Evaluate frame rate fraction string like '30000/1001'."""
    try:
        if "/" in rate_str:
            num, den = rate_str.split("/")
            return round(int(num) / int(den), 2)
        return float(rate_str)
    except (ValueError, ZeroDivisionError):
        return 0


def format_duration(seconds):
    """Format seconds to HH:MM:SS.ms."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"


def format_size(bytes_val):
    """Format bytes to human readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def cmd_info(args):
    """Show media file info."""
    result = probe(args.input)
    print(json.dumps(result, indent=2))


def cmd_cut(args):
    """Cut a segment from a video."""
    cmd = ["ffmpeg", "-y", "-i", args.input]
    if args.start:
        cmd.extend(["-ss", args.start])
    if args.end:
        cmd.extend(["-to", args.end])
    elif args.duration:
        cmd.extend(["-t", args.duration])
    cmd.extend(["-c", "copy", args.output])
    result = run_cmd(cmd)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "stderr": result["stderr"][-500:] if result["returncode"] != 0 else ""}))


def cmd_merge(args):
    """Concatenate multiple videos."""
    # Create concat file
    concat_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for f in args.inputs:
        concat_file.write(f"file '{os.path.abspath(f)}'\n")
    concat_file.close()

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file.name]
    if args.reencode:
        cmd.extend(["-c:v", "libx264", "-c:a", "aac"])
    else:
        cmd.extend(["-c", "copy"])
    cmd.append(args.output)
    result = run_cmd(cmd, timeout=600)
    os.unlink(concat_file.name)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "files_merged": len(args.inputs)}))


def cmd_extract_audio(args):
    """Extract audio from video."""
    ext = os.path.splitext(args.output)[1].lower()
    codec_map = {".mp3": "libmp3lame", ".aac": "aac", ".opus": "libopus",
                 ".wav": "pcm_s16le", ".flac": "flac", ".ogg": "libvorbis"}
    codec = codec_map.get(ext, "copy")
    cmd = ["ffmpeg", "-y", "-i", args.input, "-vn", "-c:a", codec]
    if args.bitrate:
        cmd.extend(["-b:a", args.bitrate])
    cmd.append(args.output)
    result = run_cmd(cmd)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "codec": codec}))


def cmd_subtitles(args):
    """Burn subtitles into video."""
    srt_path = args.srt.replace("\\", "/").replace(":", "\\\\:")
    cmd = ["ffmpeg", "-y", "-i", args.input,
           "-vf", f"subtitles={srt_path}",
           "-c:v", "libx264", "-c:a", "copy",
           args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_resize(args):
    """Resize video."""
    scale = f"scale={args.width}:{args.height}"
    cmd = ["ffmpeg", "-y", "-i", args.input,
           "-vf", scale, "-c:v", "libx264", "-c:a", "copy",
           args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "resolution": f"{args.width}x{args.height}"}))


def cmd_gif(args):
    """Convert video segment to GIF."""
    filters = f"fps={args.fps},scale={args.width}:-1:flags=lanczos"
    # Two-pass for quality
    palette = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    cmd1 = ["ffmpeg", "-y", "-i", args.input]
    if args.start:
        cmd1.extend(["-ss", args.start])
    if args.duration:
        cmd1.extend(["-t", args.duration])
    cmd1.extend(["-vf", f"{filters},palettegen", palette])
    run_cmd(cmd1)

    cmd2 = ["ffmpeg", "-y", "-i", args.input]
    if args.start:
        cmd2.extend(["-ss", args.start])
    if args.duration:
        cmd2.extend(["-t", args.duration])
    cmd2.extend(["-i", palette, "-lavfi", f"{filters} [x]; [x][1:v] paletteuse",
                 args.output])
    result = run_cmd(cmd2)
    os.unlink(palette)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_thumbnail(args):
    """Extract a single frame as image."""
    cmd = ["ffmpeg", "-y", "-i", args.input, "-ss", args.time,
           "-vframes", "1", args.output]
    result = run_cmd(cmd)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_thumbnails(args):
    """Extract multiple evenly-spaced thumbnails."""
    info = probe(args.input)
    duration = info.get("format", {}).get("duration", 0)
    if duration <= 0:
        print(json.dumps({"error": "Could not determine duration"}))
        return

    interval = duration / (args.count + 1)
    output_dir = args.output_dir or os.path.dirname(args.input) or "."
    os.makedirs(output_dir, exist_ok=True)

    files = []
    base = Path(args.input).stem
    for i in range(1, args.count + 1):
        ts = interval * i
        out = os.path.join(output_dir, f"{base}_thumb_{i:03d}.jpg")
        cmd = ["ffmpeg", "-y", "-ss", str(ts), "-i", args.input,
               "-vframes", "1", "-q:v", "2", out]
        run_cmd(cmd)
        files.append(out)

    print(json.dumps({"status": "ok", "thumbnails": files, "count": len(files)}))


def cmd_compress(args):
    """Compress video with target quality or size."""
    cmd = ["ffmpeg", "-y", "-i", args.input, "-c:v", "libx264"]
    if args.crf:
        cmd.extend(["-crf", str(args.crf)])
    else:
        cmd.extend(["-crf", "28"])
    if args.preset:
        cmd.extend(["-preset", args.preset])
    else:
        cmd.extend(["-preset", "medium"])
    cmd.extend(["-c:a", "aac", "-b:a", "128k", args.output])
    result = run_cmd(cmd, timeout=1200)

    output_info = {}
    if result["returncode"] == 0:
        orig_size = os.path.getsize(args.input)
        new_size = os.path.getsize(args.output)
        output_info = {
            "original_size": format_size(orig_size),
            "compressed_size": format_size(new_size),
            "reduction": f"{(1 - new_size/orig_size)*100:.1f}%",
        }
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, **output_info}))


def cmd_speed(args):
    """Change playback speed."""
    video_filter = f"setpts={1/args.factor}*PTS"
    audio_filter = f"atempo={args.factor}"
    # atempo only supports 0.5-2.0, chain for larger ranges
    if args.factor > 2.0:
        audio_filter = "atempo=2.0," * int(args.factor // 2) + f"atempo={args.factor % 2 or 2.0}"
    elif args.factor < 0.5:
        audio_filter = "atempo=0.5," * int(2 // args.factor) + f"atempo={args.factor * (2 ** int(1/args.factor))}"

    cmd = ["ffmpeg", "-y", "-i", args.input,
           "-vf", video_filter, "-af", audio_filter,
           "-c:v", "libx264", "-c:a", "aac", args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "speed": f"{args.factor}x"}))


def cmd_watermark(args):
    """Add image watermark overlay."""
    position_map = {
        "top-left": "10:10",
        "top-right": "W-w-10:10",
        "bottom-left": "10:H-h-10",
        "bottom-right": "W-w-10:H-h-10",
        "center": "(W-w)/2:(H-h)/2",
    }
    pos = position_map.get(args.position, args.position)
    overlay = f"overlay={pos}"

    cmd = ["ffmpeg", "-y", "-i", args.input, "-i", args.watermark,
           "-filter_complex", overlay,
           "-c:v", "libx264", "-c:a", "copy", args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "position": args.position}))


def cmd_text(args):
    """Burn text overlay onto video."""
    # Escape special characters for drawtext
    text = args.text.replace("'", "'\\\\\\''").replace(":", "\\\\:")
    font_size = args.size or 48
    color = args.color or "white"
    border = f":borderw=2:bordercolor=black" if args.border else ""
    position_map = {
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "top": "x=(w-text_w)/2:y=30",
        "bottom": "x=(w-text_w)/2:y=h-text_h-30",
        "top-left": "x=30:y=30",
        "bottom-right": "x=w-text_w-30:y=h-text_h-30",
    }
    pos = position_map.get(args.position, args.position or "center")

    drawtext = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={color}:{pos}{border}"

    if args.start or args.end:
        enable_parts = []
        if args.start:
            enable_parts.append(f"gte(t\\,{args.start})")
        if args.end:
            enable_parts.append(f"lte(t\\,{args.end})")
        enable = "*".join(enable_parts)
        drawtext += f":enable='{enable}'"

    cmd = ["ffmpeg", "-y", "-i", args.input,
           "-vf", drawtext,
           "-c:v", "libx264", "-c:a", "copy", args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_convert(args):
    """Convert between formats."""
    cmd = ["ffmpeg", "-y", "-i", args.input]
    if args.video_codec:
        cmd.extend(["-c:v", args.video_codec])
    if args.audio_codec:
        cmd.extend(["-c:a", args.audio_codec])
    if args.video_codec is None and args.audio_codec is None:
        pass  # Let ffmpeg choose based on output extension
    cmd.append(args.output)
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_frames(args):
    """Extract all frames or every Nth frame as images."""
    output_dir = args.output_dir or "."
    os.makedirs(output_dir, exist_ok=True)
    base = Path(args.input).stem

    cmd = ["ffmpeg", "-y", "-i", args.input]
    if args.every:
        cmd.extend(["-vf", f"select=not(mod(n\\,{args.every}))"])
        cmd.extend(["-vsync", "vfr"])
    cmd.extend([os.path.join(output_dir, f"{base}_frame_%05d.png")])
    result = run_cmd(cmd, timeout=600)

    # Count generated frames
    count = len([f for f in os.listdir(output_dir) if f.startswith(f"{base}_frame_")])
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "frames_extracted": count, "output_dir": output_dir}))


def cmd_audio_replace(args):
    """Replace video's audio track."""
    cmd = ["ffmpeg", "-y", "-i", args.input, "-i", args.audio,
           "-c:v", "copy", "-c:a", "aac",
           "-map", "0:v:0", "-map", "1:a:0",
           "-shortest", args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_volume(args):
    """Adjust audio volume."""
    cmd = ["ffmpeg", "-y", "-i", args.input,
           "-af", f"volume={args.level}",
           "-c:v", "copy", args.output]
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output, "volume": args.level}))


def cmd_fade(args):
    """Add fade in/out effects."""
    filters = []
    if args.fade_in:
        filters.append(f"fade=t=in:st=0:d={args.fade_in}")
    if args.fade_out:
        info = probe(args.input)
        duration = info.get("format", {}).get("duration", 0)
        start = max(0, duration - args.fade_out)
        filters.append(f"fade=t=out:st={start}:d={args.fade_out}")

    audio_filters = []
    if args.fade_in:
        audio_filters.append(f"afade=t=in:st=0:d={args.fade_in}")
    if args.fade_out:
        info = probe(args.input)
        duration = info.get("format", {}).get("duration", 0)
        start = max(0, duration - args.fade_out)
        audio_filters.append(f"afade=t=out:st={start}:d={args.fade_out}")

    cmd = ["ffmpeg", "-y", "-i", args.input]
    if filters:
        cmd.extend(["-vf", ",".join(filters)])
    if audio_filters:
        cmd.extend(["-af", ",".join(audio_filters)])
    cmd.extend(["-c:v", "libx264", "-c:a", "aac", args.output])
    result = run_cmd(cmd, timeout=600)
    print(json.dumps({"status": "ok" if result["returncode"] == 0 else "error",
                       "output": args.output}))


def cmd_stabilize(args):
    """Two-pass video stabilization using vidstab."""
    transforms = tempfile.NamedTemporaryFile(suffix=".trf", delete=False).name
    # Pass 1: analyze
    cmd1 = ["ffmpeg", "-y", "-i", args.input,
            "-vf", f"vidstabdetect=shakiness={args.shakiness}:result={transforms}",
            "-f", "null", "-"]
    result1 = run_cmd(cmd1, timeout=600)
    if result1["returncode"] != 0:
        print(json.dumps({"error": "stabilization analysis failed", "stderr": result1["stderr"][-300:]}))
        return

    # Pass 2: transform
    cmd2 = ["ffmpeg", "-y", "-i", args.input,
            "-vf", f"vidstabtransform=input={transforms}:smoothing={args.smoothing},unsharp",
            "-c:v", "libx264", "-c:a", "copy", args.output]
    result2 = run_cmd(cmd2, timeout=600)
    os.unlink(transforms)
    print(json.dumps({"status": "ok" if result2["returncode"] == 0 else "error",
                       "output": args.output}))


def main():
    parser = argparse.ArgumentParser(description="fftools — High-level ffmpeg wrapper")
    subparsers = parser.add_subparsers(dest="command")

    # info
    p = subparsers.add_parser("info", help="Show media file info")
    p.add_argument("input")

    # cut
    p = subparsers.add_parser("cut", help="Cut a video segment")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--start", "-ss")
    p.add_argument("--end", "-to")
    p.add_argument("--duration", "-t")

    # merge
    p = subparsers.add_parser("merge", help="Concatenate videos")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--reencode", action="store_true")

    # extract-audio
    p = subparsers.add_parser("extract-audio", help="Extract audio track")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--bitrate", "-b")

    # subtitles
    p = subparsers.add_parser("subtitles", help="Burn subtitles into video")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--srt", required=True)

    # resize
    p = subparsers.add_parser("resize", help="Resize video")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--width", "-w", default="-1")
    p.add_argument("--height", type=str, default="-1")

    # gif
    p = subparsers.add_parser("gif", help="Convert video to GIF")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--fps", type=int, default=15)
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--start", "-ss")
    p.add_argument("--duration", "-t")

    # thumbnail
    p = subparsers.add_parser("thumbnail", help="Extract single frame")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--time", "-t", default="00:00:01")

    # thumbnails
    p = subparsers.add_parser("thumbnails", help="Extract evenly-spaced thumbnails")
    p.add_argument("input")
    p.add_argument("--count", "-n", type=int, default=5)
    p.add_argument("--output-dir", "-o")

    # compress
    p = subparsers.add_parser("compress", help="Compress video")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--crf", type=int, help="Quality (0=lossless, 51=worst, default 28)")
    p.add_argument("--preset", help="Speed preset (ultrafast..veryslow)")

    # speed
    p = subparsers.add_parser("speed", help="Change playback speed")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--factor", "-x", type=float, required=True, help="Speed multiplier (2.0 = 2x faster)")

    # watermark
    p = subparsers.add_parser("watermark", help="Add image watermark")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--watermark", "-w", required=True, help="Watermark image")
    p.add_argument("--position", "-p", default="bottom-right",
                   choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"])

    # text
    p = subparsers.add_parser("text", help="Add text overlay")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--text", required=True)
    p.add_argument("--position", "-p", default="center")
    p.add_argument("--size", type=int)
    p.add_argument("--color")
    p.add_argument("--border", action="store_true")
    p.add_argument("--start", type=float, help="Show text from this second")
    p.add_argument("--end", type=float, help="Hide text after this second")

    # convert
    p = subparsers.add_parser("convert", help="Convert format")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--video-codec", "-vc")
    p.add_argument("--audio-codec", "-ac")

    # frames
    p = subparsers.add_parser("frames", help="Extract frames as images")
    p.add_argument("input")
    p.add_argument("--output-dir", "-o")
    p.add_argument("--every", type=int, help="Extract every Nth frame")

    # audio-replace
    p = subparsers.add_parser("audio-replace", help="Replace audio track")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--audio", "-a", required=True)

    # volume
    p = subparsers.add_parser("volume", help="Adjust audio volume")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--level", "-l", required=True, help="Volume level (2.0 = 2x, 0.5 = half, 10dB, -5dB)")

    # fade
    p = subparsers.add_parser("fade", help="Add fade in/out")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--fade-in", type=float, help="Fade in duration (seconds)")
    p.add_argument("--fade-out", type=float, help="Fade out duration (seconds)")

    # stabilize
    p = subparsers.add_parser("stabilize", help="Stabilize shaky video")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--shakiness", type=int, default=5, help="1-10, detection sensitivity")
    p.add_argument("--smoothing", type=int, default=10, help="Smoothing strength")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "info": cmd_info, "cut": cmd_cut, "merge": cmd_merge,
        "extract-audio": cmd_extract_audio, "subtitles": cmd_subtitles,
        "resize": cmd_resize, "gif": cmd_gif, "thumbnail": cmd_thumbnail,
        "thumbnails": cmd_thumbnails, "compress": cmd_compress,
        "speed": cmd_speed, "watermark": cmd_watermark, "text": cmd_text,
        "convert": cmd_convert, "frames": cmd_frames,
        "audio-replace": cmd_audio_replace, "volume": cmd_volume,
        "fade": cmd_fade, "stabilize": cmd_stabilize,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
