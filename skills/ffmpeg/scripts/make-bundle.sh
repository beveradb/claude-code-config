#!/usr/bin/env bash
#
# make-bundle.sh — package EVERYTHING needed to install `transcribe` on another
# machine with NO access to HuggingFace or PyPI. Produces a single .tar.gz you can
# host on your own server; a target machine then runs:
#
#     bash install-transcribe.sh --bundle https://your.server/ffmpeg-transcribe-bundle.tar.gz
#
# The bundle contains: scripts, sherpa-onnx diarization models, the WhisperX model
# caches (large-v3 + English alignment + VAD), pinned requirements, and a full
# wheelhouse (all Python deps as wheels for THIS platform).
#
# Run this on a machine where install-transcribe.sh has already completed.
#
# Usage:  bash make-bundle.sh [output.tar.gz]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PY="$SKILL_DIR/.venv/bin/python"
MODELS_DIR="$SKILL_DIR/models"
OUT="${1:-$SKILL_DIR/ffmpeg-transcribe-bundle.tar.gz}"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

[ -x "$VENV_PY" ] || { err "venv not found — run install-transcribe.sh first"; exit 1; }
command -v uv >/dev/null 2>&1 || { err "uv is required"; exit 1; }

STAGE="$(mktemp -d)"
BUNDLE="$STAGE/bundle"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$BUNDLE/skill" "$BUNDLE/models" "$BUNDLE/hf-cache" "$BUNDLE/torch-cache" "$BUNDLE/wheels"

# --- 1. Code ----------------------------------------------------------------
log "Copying scripts"
cp "$SCRIPT_DIR/fftools.py" "$SCRIPT_DIR/transcribe_worker.py" \
   "$SCRIPT_DIR/install-transcribe.sh" "$SCRIPT_DIR/make-bundle.sh" "$BUNDLE/skill/"
[ -f "$SKILL_DIR/SKILL.md" ] && cp "$SKILL_DIR/SKILL.md" "$BUNDLE/skill/"

# --- 2. sherpa-onnx diarization models --------------------------------------
log "Copying sherpa-onnx diarization models"
cp -R "$MODELS_DIR/sherpa-onnx-pyannote-segmentation-3-0" "$BUNDLE/models/"
cp "$MODELS_DIR/nemo_en_titanet_large.onnx" "$BUNDLE/models/"

# --- 3. WhisperX model caches (minimal subset) ------------------------------
# Cherry-pick only the two models a fresh install needs — whisper large-v3 (HF
# cache) and the English wav2vec2 alignment model (torch cache) — from the local
# caches. Then verify they load OFFLINE from the bundle; if anything is missing,
# fall back to a redirected re-download that captures exactly what's required.
log "Staging WhisperX model caches (minimal copy)"
DEF_HF="${HF_HOME:-$HOME/.cache/huggingface}"
DEF_TORCH="${TORCH_HOME:-$HOME/.cache/torch}"
mkdir -p "$BUNDLE/hf-cache/hub" "$BUNDLE/torch-cache/hub/checkpoints"

for d in "$DEF_HF"/hub/models--Systran--faster-whisper-large-v3 "$DEF_HF"/hub/models--pyannote--*; do
    [ -e "$d" ] && cp -R "$d" "$BUNDLE/hf-cache/hub/"
done
# English alignment model checkpoint (torchaudio bundle)
cp "$DEF_TORCH"/hub/checkpoints/wav2vec2_fairseq_base_ls960_asr_ls960.pth \
   "$BUNDLE/torch-cache/hub/checkpoints/" 2>/dev/null || true

log "Verifying model caches load offline"
if ! HF_HOME="$BUNDLE/hf-cache" TORCH_HOME="$BUNDLE/torch-cache" \
      HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "$VENV_PY" - <<'PY' 2>/dev/null
import whisperx
whisperx.load_model("large-v3", device="cpu", compute_type="int8")
whisperx.load_align_model(language_code="en", device="cpu")
print("ok")
PY
then
    log "Offline verify failed — re-downloading a clean minimal cache into the bundle"
    rm -rf "$BUNDLE/hf-cache" "$BUNDLE/torch-cache"
    mkdir -p "$BUNDLE/hf-cache" "$BUNDLE/torch-cache"
    HF_HOME="$BUNDLE/hf-cache" TORCH_HOME="$BUNDLE/torch-cache" \
        HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 "$VENV_PY" - <<'PY'
import whisperx
whisperx.load_model("large-v3", device="cpu", compute_type="int8")
whisperx.load_align_model(language_code="en", device="cpu")
print("model caches staged")
PY
fi

# --- 4. Wheelhouse (all deps as wheels for this platform) -------------------
log "Freezing dependencies and downloading wheels"
uv pip freeze --python "$VENV_PY" | grep -v '^-e ' > "$BUNDLE/requirements.txt"
# uv has no `pip download`; add pip to the venv, then use it to build the wheelhouse.
uv pip install --python "$VENV_PY" pip >/dev/null
"$VENV_PY" -m pip download -r "$BUNDLE/requirements.txt" -d "$BUNDLE/wheels" \
    --only-binary=:all: 2>/dev/null \
  || "$VENV_PY" -m pip download -r "$BUNDLE/requirements.txt" -d "$BUNDLE/wheels"

# --- 5. Manifest + archive --------------------------------------------------
{
    echo "ffmpeg transcribe bundle"
    echo "platform: $(uname -sm)"
    echo "python: $("$VENV_PY" --version 2>&1)"
    echo "wheels: $(ls "$BUNDLE/wheels" | wc -l | tr -d ' ')"
    echo "requirements:"
    sed 's/^/  /' "$BUNDLE/requirements.txt"
} > "$BUNDLE/MANIFEST.txt"

log "Creating archive $OUT"
tar czf "$OUT" -C "$STAGE" bundle
log "Bundle size: $(du -sh "$OUT" | cut -f1)"

# Split into <2GB parts so it fits typical upload/hosting limits. Parts are named
# <OUT>.part-aa, <OUT>.part-ab, ...  Reassemble with: cat <OUT>.part-* > <OUT>
SPLIT_SIZE="1900m"
BYTES=$(wc -c < "$OUT")
if [ "$BYTES" -gt 2000000000 ]; then
    log "Splitting into ${SPLIT_SIZE} parts (over 2GB)"
    rm -f "$OUT".part-*
    split -b "$SPLIT_SIZE" "$OUT" "$OUT".part-
    rm -f "$OUT"
    log "Done. Parts:"
    ls -lh "$OUT".part-* | awk '{print "  " $9 "  (" $5 ")"}'
    echo "Host the parts, then on a target machine (order matters):"
    echo "  bash install-transcribe.sh --bundle <url-to-part-aa> <url-to-part-ab> ..."
else
    log "Done (single file, under 2GB)."
    echo "Host $OUT, then on a target machine:"
    echo "  bash install-transcribe.sh --bundle <url-or-path-to-bundle.tar.gz>"
fi
