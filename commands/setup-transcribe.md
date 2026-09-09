---
description: Install/repair the ffmpeg skill's offline transcribe + diarization tooling (WhisperX + sherpa-onnx)
allowed-tools: Bash, Read
---

# Setup Transcribe

Install (or repair) the fully-offline speech transcription + speaker diarization
tooling behind the `ffmpeg` skill's `transcribe` command (WhisperX large-v3 for ASR
+ word timestamps, sherpa-onnx for token-free diarization). Everything runs locally;
audio never leaves the machine.

**Optional argument** ($ARGUMENTS): install mode —
- _(empty)_ → **auto**: fetch the prebuilt GitHub release bundle, falling back to a
  from-scratch build if the release is unavailable or the platform's wheels don't match
- `release` → force install from the release bundle only
- `build` → force a from-scratch build (downloads models from HuggingFace + wheels from PyPI)
- `HF_TOKEN=hf_xxx … build` → also pre-download the opt-in `--diarizer pyannote` pipeline

## Instructions

### 1. Preconditions
Verify `uv` and `ffmpeg` are on PATH. If either is missing, tell the user to run
`brew install uv ffmpeg` and stop.

### 2. Check if already installed
If `~/.claude/skills/ffmpeg/.venv/bin/python` and
`~/.claude/skills/ffmpeg/models/nemo_en_titanet_large.onnx` already exist, report that
it's already installed and ask whether to reinstall before proceeding (unless the user
passed an explicit mode argument).

### 3. Map the argument to an installer flag
- empty → _(no flag; auto mode)_
- `release` → `--release`
- `build` → `--build`

### 4. Run the installer (long-running — downloads several GB)
Run in the **background** and poll the output file, because it downloads a large
bundle or torch + a ~3GB model cache:

```bash
bash ~/.claude/skills/ffmpeg/scripts/install-transcribe.sh <flag>
```

Use `run_in_background: true`, then read the task output file periodically until the
process exits. Surface progress milestones (downloading, extracting, caching) to the
user. Do not block the whole time in one call.

### 5. Verify
On exit code 0, confirm the CLI is wired up:

```bash
python3 ~/.claude/skills/ffmpeg/scripts/fftools.py transcribe --help
```

If the user has a short sample media file handy, optionally offer to run a real
transcription. Do not fabricate a test file unless asked.

### 6. Report
Summarize: which mode ran (release vs build), where the venv + models live, and the
usage:

```bash
python3 ~/.claude/skills/ffmpeg/scripts/fftools.py transcribe meeting.mp4
```

If the installer fell back from `release` to `build`, note that (the release assets
may not have been reachable). If it failed, show the last ~20 lines of output and
suggest `build` mode as a fallback.
