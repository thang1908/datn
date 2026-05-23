"""Node: Validate audio bytes từ file upload (thay thế download_audio)."""

import logging

from ..state import CallState

logger = logging.getLogger(__name__)

_SUPPORTED_FORMATS = {"wav", "mp3", "m4a", "flac", "ogg"}


async def read_audio(state: CallState) -> dict:
    """
    Validate và chuẩn bị audio bytes đã được upload.

    Bytes được truyền trực tiếp vào state từ route handler,
    không cần download từ URL nữa.
    """
    audio_bytes = state.get("audio_bytes")
    audio_format = state.get("audio_format", "wav")

    if not audio_bytes:
        raise ValueError("No audio bytes in state — missing file upload")

    if audio_format not in _SUPPORTED_FORMATS:
        logger.warning(f"Unknown audio format '{audio_format}', defaulting to 'wav'")
        audio_format = "wav"

    logger.info(f"Audio ready: format={audio_format}, size={len(audio_bytes):,} bytes")
    return {
        "audio_bytes": audio_bytes,
        "audio_format": audio_format,
    }
