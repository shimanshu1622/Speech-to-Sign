import os
from faster_whisper import WhisperModel

# CONFIG

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")  # "cuda" if GPU
WHISPER_COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8" if WHISPER_DEVICE == "cpu" else "float16"
)

# LOAD MODEL ONCE 

_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device="cpu",
    compute_type="int8",
)

# MAIN FUNCTION

def speech_to_text(audio_path: str) -> str:
    """
    Transcribe speech audio file → English text.
    Deterministic, offline, fast.
    """

    segments, info = _model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,      # ignore silence
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    text_parts = []
    for segment in segments:
        if segment.text:
            text_parts.append(segment.text.strip())

    text = " ".join(text_parts).strip()

    return text