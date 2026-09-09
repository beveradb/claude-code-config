#!/usr/bin/env python3
"""
transcribe_worker.py — runs INSIDE the ffmpeg skill's dedicated venv (.venv).

Transcribes a 16kHz mono WAV with WhisperX (word-level timestamps) and assigns
speaker labels via diarization, then writes .json / .srt / .txt outputs.

Everything runs locally and offline. Two diarizers:
  * sherpa  (default) — token-free ONNX models (pyannote-segmentation-3.0 + NeMo TitaNet)
  * pyannote (opt-in) — needs a one-time HF token; higher quality

Not meant to be called directly — the `transcribe` subcommand in fftools.py invokes
it with the right venv interpreter. Prints a single JSON summary object to stdout.
"""
import argparse
import json
import os
import sys
import warnings

# Silence the benign torchcodec/libavutil UserWarning (whisperx loads audio via the
# ffmpeg CLI, not torchcodec) and other import-time warnings, so stdout stays clean JSON.
warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONWARNINGS", "ignore")

# Prefer skill-local model caches when present (populated by an offline bundle), so the
# install is self-contained. Falls back to the user's default caches otherwise.
_MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
if os.path.isdir(os.path.join(_MODELS, "hf-cache")):
    os.environ.setdefault("HF_HOME", os.path.join(_MODELS, "hf-cache"))
if os.path.isdir(os.path.join(_MODELS, "torch-cache")):
    os.environ.setdefault("TORCH_HOME", os.path.join(_MODELS, "torch-cache"))

# Force fully-offline model loading (models are pre-cached by install-transcribe.sh).
# --allow-download flips this off so a first-time pyannote fetch can hit the network.
if "--allow-download" not in sys.argv:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def fmt_ts(seconds, sep=","):
    """Seconds -> SRT timestamp HH:MM:SS,mmm."""
    if seconds is None:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def spk_label(spk):
    """Normalize a speaker id (int or 'SPEAKER_XX') to 'SPEAKER_00'."""
    if spk is None:
        return "SPEAKER_?"
    s = str(spk)
    if s.startswith("SPEAKER_"):
        return s
    try:
        return f"SPEAKER_{int(s):02d}"
    except ValueError:
        return s


def diarize_sherpa(wav, seg_model, emb_model, num_speakers, cluster_threshold):
    """Token-free diarization with sherpa-onnx. Returns list of (start, end, speaker)."""
    import sherpa_onnx
    import soundfile as sf

    config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=seg_model),
        ),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=emb_model),
        clustering=sherpa_onnx.FastClusteringConfig(
            num_clusters=num_speakers if num_speakers and num_speakers > 0 else -1,
            threshold=cluster_threshold,
        ),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    if not config.validate():
        raise RuntimeError("sherpa-onnx diarization config failed validation (check model paths)")

    sd = sherpa_onnx.OfflineSpeakerDiarization(config)
    audio, sample_rate = sf.read(wav, dtype="float32", always_2d=True)
    audio = audio[:, 0]  # mono
    if sample_rate != sd.sample_rate:
        raise RuntimeError(
            f"Audio is {sample_rate}Hz but diarizer expects {sd.sample_rate}Hz "
            "(the caller should extract 16kHz mono WAV)"
        )

    result = sd.process(audio).sort_by_start_time()
    return [(seg.start, seg.end, spk_label(seg.speaker)) for seg in result]


def diarize_pyannote(wav, hf_token, num_speakers, device):
    """Opt-in diarization with pyannote via whisperx. Returns a diarize DataFrame."""
    try:
        from whisperx.diarize import DiarizationPipeline
    except Exception:
        from whisperx import DiarizationPipeline  # older layout
    kwargs = {"device": device}
    if hf_token:
        kwargs["use_auth_token"] = hf_token
    pipe = DiarizationPipeline(**kwargs)
    if num_speakers and num_speakers > 0:
        return pipe(wav, num_speakers=num_speakers)
    return pipe(wav)


def main():
    ap = argparse.ArgumentParser(description="WhisperX + diarization worker (runs in venv)")
    ap.add_argument("--audio", required=True, help="16kHz mono WAV input")
    ap.add_argument("--output-base", required=True, help="Output path without extension")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--language", default=None, help="Force language code (e.g. en); auto-detect if unset")
    ap.add_argument("--diarizer", default="sherpa", choices=["sherpa", "pyannote", "none"])
    ap.add_argument("--speakers", type=int, default=0, help="Known speaker count (0 = auto)")
    ap.add_argument("--cluster-threshold", type=float, default=0.5, help="sherpa clustering threshold")
    ap.add_argument("--seg-model", default=None, help="sherpa segmentation model.onnx")
    ap.add_argument("--emb-model", default=None, help="sherpa embedding .onnx")
    ap.add_argument("--hf-token", default=None, help="HF token for pyannote diarizer")
    ap.add_argument("--formats", default="json,srt,txt")
    ap.add_argument("--compute-type", default="int8", help="ctranslate2 compute type (int8/float32)")
    ap.add_argument("--allow-download", action="store_true", help="Permit network model downloads")
    args = ap.parse_args()

    import whisperx
    try:
        from whisperx.diarize import assign_word_speakers
    except Exception:
        from whisperx import assign_word_speakers

    device = "cpu"  # ctranslate2 has no MPS backend on Apple Silicon

    # --- 1. Transcribe ------------------------------------------------------
    audio = whisperx.load_audio(args.audio)
    asr_kwargs = {}
    if args.language:
        asr_kwargs["language"] = args.language
    model = whisperx.load_model(args.model, device, compute_type=args.compute_type, **asr_kwargs)
    result = model.transcribe(audio, batch_size=16)
    language = result.get("language", args.language or "en")

    # --- 2. Align (word-level timestamps) -----------------------------------
    aligned = False
    try:
        align_model, metadata = whisperx.load_align_model(language_code=language, device=device)
        result = whisperx.align(
            result["segments"], align_model, metadata, audio, device,
            return_char_alignments=False,
        )
        aligned = True
    except Exception as e:
        # Alignment model may not exist for some languages; continue with segment-level times.
        print(f"[transcribe_worker] alignment skipped: {e}", file=sys.stderr)

    # --- 3. Diarize + assign speakers ---------------------------------------
    diarizer_used = args.diarizer
    num_speakers = None
    try:
        if args.diarizer == "sherpa":
            segs = diarize_sherpa(
                args.audio, args.seg_model, args.emb_model,
                args.speakers, args.cluster_threshold,
            )
            import pandas as pd
            diarize_df = pd.DataFrame(segs, columns=["start", "end", "speaker"])
            result = assign_word_speakers(diarize_df, result)
            num_speakers = int(diarize_df["speaker"].nunique()) if not diarize_df.empty else 0
        elif args.diarizer == "pyannote":
            diarize_df = diarize_pyannote(args.audio, args.hf_token, args.speakers, device)
            result = assign_word_speakers(diarize_df, result)
            try:
                num_speakers = int(diarize_df["speaker"].nunique())
            except Exception:
                num_speakers = None
    except Exception as e:
        print(f"[transcribe_worker] diarization failed ({e}); writing transcript without speakers",
              file=sys.stderr)
        diarizer_used = "none"

    segments = result.get("segments", [])

    # --- 4. Write outputs ---------------------------------------------------
    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    outputs = {}

    if "json" in formats:
        path = args.output_base + ".json"
        with open(path, "w") as f:
            json.dump({"language": language, "segments": segments}, f, indent=2, ensure_ascii=False)
        outputs["json"] = path

    if "srt" in formats:
        path = args.output_base + ".srt"
        with open(path, "w") as f:
            for i, seg in enumerate(segments, 1):
                spk = seg.get("speaker")
                text = seg.get("text", "").strip()
                prefix = f"[{spk_label(spk)}] " if spk else ""
                f.write(f"{i}\n{fmt_ts(seg.get('start'))} --> {fmt_ts(seg.get('end'))}\n{prefix}{text}\n\n")
        outputs["srt"] = path

    if "txt" in formats:
        path = args.output_base + ".txt"
        with open(path, "w") as f:
            current = None
            for seg in segments:
                spk = spk_label(seg.get("speaker")) if seg.get("speaker") else None
                text = seg.get("text", "").strip()
                if not text:
                    continue
                if spk and spk != current:
                    ts = fmt_ts(seg.get("start"), sep=".")[:8]  # HH:MM:SS
                    f.write(f"\n[{ts}] {spk}:\n")
                    current = spk
                elif spk is None and current != "__plain__":
                    current = "__plain__"
                f.write(text + " ")
            f.write("\n")
        outputs["txt"] = path

    duration = segments[-1].get("end") if segments else 0
    print(json.dumps({
        "status": "ok",
        "language": language,
        "model": args.model,
        "diarizer": diarizer_used,
        "aligned": aligned,
        "num_speakers": num_speakers,
        "num_segments": len(segments),
        "duration_sec": round(duration or 0, 2),
        "outputs": outputs,
    }))


if __name__ == "__main__":
    main()
