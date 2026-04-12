"""Lazy-loaded Whisper for the web server (avoid importing listener/sounddevice)."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        name = (os.environ.get("WHISPER_MODEL") or "base").strip() or "base"
        _model = WhisperModel(name, device="cpu", compute_type="int8")
    return _model


def transcribe_wav_path(wav_path: str) -> str:
    model = _get_model()
    lang = (os.environ.get("WHISPER_LANGUAGE") or "en").strip() or "en"
    if lang.lower() in ("auto", "detect"):
        segments, _ = model.transcribe(wav_path, beam_size=5, vad_filter=False)
    else:
        segments, _ = model.transcribe(
            wav_path, language=lang, beam_size=5, vad_filter=False
        )
    return " ".join(s.text for s in segments).strip()


def transcribe_uploaded_audio(raw: bytes, filename: str | None) -> str:
    """
    Convert browser recording (webm/ogg/wav/…) to 16 kHz mono WAV via ffmpeg, then Whisper.
    Requires ffmpeg on PATH.
    """
    if len(raw) < 64:
        return ""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg not found on PATH — install it for Call mode (e.g. apt install ffmpeg)."
        )
    suffix = Path(filename or "clip.webm").suffix.lower()
    if suffix not in (".webm", ".ogg", ".opus", ".wav", ".mp4", ".m4a", ""):
        suffix = ".webm"
    in_f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        in_f.write(raw)
        in_f.close()
        out_path = in_f.name + ".wav"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                in_f.name,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                out_path,
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return transcribe_wav_path(out_path)
    finally:
        Path(in_f.name).unlink(missing_ok=True)
        Path(in_f.name + ".wav").unlink(missing_ok=True)
