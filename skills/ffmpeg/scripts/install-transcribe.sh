#!/usr/bin/env bash
#
# install-transcribe.sh — one-time setup for the ffmpeg skill's `transcribe` command.
#
# Sets up an isolated Python 3.12 venv (via uv) with WhisperX + sherpa-onnx and all
# models, so transcription + speaker diarization run FULLY OFFLINE afterwards. No
# Hugging Face token is required for the default (sherpa-onnx) diarizer.
#
# Modes:
#   bash install-transcribe.sh                 # auto: fetch prebuilt release bundle, else build
#   bash install-transcribe.sh --release       # force install from the GitHub release bundle
#   bash install-transcribe.sh --build         # force a from-scratch build (downloads from HF/PyPI)
#   bash install-transcribe.sh --bundle A [B..] # install from a local/remote bundle (parts in order)
#   HF_TOKEN=hf_xxx bash install-transcribe.sh --build   # also pre-download pyannote (opt-in)
#
# The prebuilt bundle is a wheelhouse for a specific platform (macOS arm64); on any
# other platform the release install falls back to a from-scratch build automatically.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SKILL_DIR/.venv"
MODELS_DIR="$SKILL_DIR/models"
PY_VERSION="3.12"

# Where the prebuilt offline bundle lives (override via env for a fork/mirror).
REPO="${BUNDLE_REPO:-beveradb/claude-code-config}"
RELEASE_TAG="${BUNDLE_RELEASE_TAG:-assets}"
BUNDLE_PREFIX="ffmpeg-transcribe-bundle.tar.gz"
RELEASE_DL="https://github.com/$REPO/releases/download/$RELEASE_TAG"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

# --- Preconditions ----------------------------------------------------------
command -v uv >/dev/null 2>&1 || { err "uv is required (https://docs.astral.sh/uv/). Install with: brew install uv"; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || { err "ffmpeg is required. Install with: brew install ffmpeg"; exit 1; }

mkdir -p "$MODELS_DIR"

# --- Discover the release bundle parts --------------------------------------
# Queries the GitHub release for assets named <prefix>.part-* (any count), newest
# ordering by name. Falls back to the two known part URLs if the API is unavailable.
discover_release_parts() {
    local api="https://api.github.com/repos/$REPO/releases/tags/$RELEASE_TAG"
    local urls parts
    urls="$(curl -fsSL "$api" 2>/dev/null \
        | grep '"browser_download_url"' \
        | sed -E 's/.*"(https:[^"]+)".*/\1/' \
        | grep -E "/${BUNDLE_PREFIX}(\.part-|\$)" || true)"
    parts="$(printf '%s\n' "$urls" | grep '\.part-' | sort || true)"
    if [ -n "$parts" ]; then
        printf '%s\n' "$parts"
    elif [ -n "$urls" ]; then
        printf '%s\n' "$urls" | sort
    else
        # API unreachable — fall back to the known two-part layout.
        printf '%s\n' "$RELEASE_DL/${BUNDLE_PREFIX}.part-aa" "$RELEASE_DL/${BUNDLE_PREFIX}.part-ab"
    fi
}

# --- Install from a bundle (whole file or ordered split parts) ---------------
install_from_parts() {
    [ "$#" -ge 1 ] || { err "no bundle parts given"; return 1; }
    local TMP idx dest SRC B
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' RETURN

    idx=0
    for SRC in "$@"; do
        dest="$TMP/part.$(printf '%03d' "$idx")"
        if printf '%s' "$SRC" | grep -qE '^https?://'; then
            log "Downloading part $((idx + 1))/$# from $SRC"
            curl -fL "$SRC" -o "$dest"
        else
            log "Using local part $((idx + 1))/$#: $SRC"
            cp "$SRC" "$dest"
        fi
        idx=$((idx + 1))
    done

    log "Reassembling bundle from $# part(s)"
    cat "$TMP"/part.* > "$TMP/bundle.tar.gz"

    log "Extracting bundle"
    tar xzf "$TMP/bundle.tar.gz" -C "$TMP"
    B="$TMP/bundle"
    [ -d "$B/wheels" ] || { err "bundle looks invalid (no wheels/ dir)"; return 1; }

    log "Placing models and caches under $MODELS_DIR"
    cp -R "$B/models/." "$MODELS_DIR/"
    rm -rf "$MODELS_DIR/hf-cache" "$MODELS_DIR/torch-cache"
    cp -R "$B/hf-cache" "$MODELS_DIR/hf-cache"
    cp -R "$B/torch-cache" "$MODELS_DIR/torch-cache"

    log "Updating scripts from bundle"
    cp "$B/skill/"*.py "$B/skill/"*.sh "$SCRIPT_DIR/" 2>/dev/null || true
    [ -f "$B/skill/SKILL.md" ] && cp "$B/skill/SKILL.md" "$SKILL_DIR/SKILL.md"

    log "Creating venv and installing from wheelhouse (offline)"
    uv venv --python "$PY_VERSION" "$VENV_DIR"
    uv pip install --python "$VENV_DIR/bin/python" --offline --no-index \
        --find-links "$B/wheels" -r "$B/requirements.txt"

    log "Done. transcribe installed from prebuilt bundle."
    echo "  Venv:   $VENV_DIR"
    echo "  Models: $MODELS_DIR (self-contained caches)"
    return 0
}

# --- Build from scratch (downloads from HuggingFace + PyPI) ------------------
build_from_scratch() {
    local VENV_PY SEG_TAR SEG_DIR SEG_URL EMB_FILE EMB_URL

    # 1. Isolated venv — pin 3.12 (system 3.14 is too new for torch).
    log "Creating Python $PY_VERSION venv at $VENV_DIR"
    uv venv --python "$PY_VERSION" "$VENV_DIR"
    VENV_PY="$VENV_DIR/bin/python"

    # 2. Python deps.
    log "Installing whisperx + sherpa-onnx (this downloads torch — a few minutes)"
    uv pip install --python "$VENV_PY" "whisperx" "sherpa-onnx" "soundfile" "numpy"

    # 3. sherpa-onnx diarization models (token-free).
    SEG_TAR="sherpa-onnx-pyannote-segmentation-3-0.tar.bz2"
    SEG_DIR="$MODELS_DIR/sherpa-onnx-pyannote-segmentation-3-0"
    SEG_URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/$SEG_TAR"
    EMB_FILE="nemo_en_titanet_large.onnx"
    EMB_URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/$EMB_FILE"

    if [ ! -f "$SEG_DIR/model.onnx" ]; then
        log "Downloading speaker segmentation model"
        curl -fL "$SEG_URL" -o "$MODELS_DIR/$SEG_TAR"
        tar xjf "$MODELS_DIR/$SEG_TAR" -C "$MODELS_DIR"
        rm -f "$MODELS_DIR/$SEG_TAR"
    else
        log "Segmentation model already present — skipping"
    fi

    if [ ! -f "$MODELS_DIR/$EMB_FILE" ]; then
        log "Downloading speaker embedding model ($EMB_FILE)"
        curl -fL "$EMB_URL" -o "$MODELS_DIR/$EMB_FILE"
    else
        log "Embedding model already present — skipping"
    fi

    # 4. Pre-cache WhisperX models (ungated) so the first run works offline.
    log "Pre-downloading WhisperX large-v3 + alignment model (~3GB, one time)"
    "$VENV_PY" - <<'PY'
import whisperx
model = whisperx.load_model("large-v3", device="cpu", compute_type="int8")
align_model, metadata = whisperx.load_align_model(language_code="en", device="cpu")
print("WhisperX models cached.")
PY

    # 5. Optional pyannote (opt-in diarizer, needs HF token).
    if [ -n "${HF_TOKEN:-}" ]; then
        log "HF_TOKEN detected — pre-downloading pyannote diarization pipeline (opt-in)"
        if "$VENV_PY" - <<PY
import sys
try:
    from pyannote.audio import Pipeline
    Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token="${HF_TOKEN}")
    print("pyannote pipeline cached.")
except Exception as e:
    print(f"pyannote pre-download failed: {e}", file=sys.stderr)
    sys.exit(1)
PY
        then
            echo "pyannote ready. Use: transcribe ... --diarizer pyannote"
        else
            warn "pyannote pre-download failed. Ensure you accepted terms at:"
            warn "  https://hf.co/pyannote/speaker-diarization-3.1"
            warn "  https://hf.co/pyannote/segmentation-3.0"
            warn "The default (sherpa-onnx) diarizer still works with no token."
        fi
    else
        log "No HF_TOKEN set — skipping pyannote (default sherpa-onnx diarizer needs no token)"
    fi

    log "Done. transcribe is ready and runs fully offline."
    echo "  Venv:   $VENV_DIR"
    echo "  Models: $MODELS_DIR"
    return 0
}

# --- Dispatch ---------------------------------------------------------------
MODE="${1:-auto}"
case "$MODE" in
    --bundle)
        shift
        [ "$#" -ge 1 ] || { err "usage: install-transcribe.sh --bundle <url-or-path> [<part2> ...]"; exit 1; }
        install_from_parts "$@"
        ;;
    --release)
        log "Installing from GitHub release bundle ($REPO @ $RELEASE_TAG)"
        # shellcheck disable=SC2046
        install_from_parts $(discover_release_parts)
        ;;
    --build)
        build_from_scratch
        ;;
    auto|"")
        # Default: prefer the fast prebuilt release bundle; fall back to a build if
        # it fails (e.g. release not up yet, or a non-matching platform's wheels).
        log "Attempting install from prebuilt release bundle (use --build to skip)"
        if ( set -e; install_from_parts $(discover_release_parts) ); then
            :
        else
            warn "Release bundle install unavailable — falling back to a from-scratch build."
            rm -rf "$VENV_DIR"
            build_from_scratch
        fi
        ;;
    *)
        err "unknown option: $MODE"
        err "usage: install-transcribe.sh [--release | --build | --bundle <parts...>]"
        exit 1
        ;;
esac

echo ""
echo "Try:  python3 $SCRIPT_DIR/fftools.py transcribe your-meeting.mp4"
