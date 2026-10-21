import logging
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings

logger = logging.getLogger("compania-bot.stt")

_model: WhisperModel | None = None


def cargar_modelo() -> None:
    """Se llama en el startup de FastAPI para evitar latencia en el primer request."""
    global _model
    if _model is None:
        logger.info("Cargando Whisper '%s'...", settings.whisper_model_size)
        _model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
        logger.info("Whisper listo.")


def transcribir(ruta_audio: str | Path, idioma: str = "es") -> str:
    if _model is None:
        cargar_modelo()
    segmentos, _ = _model.transcribe(str(ruta_audio), beam_size=5, language=idioma)
    return " ".join(s.text.strip() for s in segmentos).strip()