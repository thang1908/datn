"""Node: Download audio from URL into memory."""

import logging
from pathlib import PurePosixPath
from urllib.parse import urlparse

import httpx
from langchain_core.runnables import RunnableConfig

from ..state import CallState

logger = logging.getLogger(__name__)

_MIME_TO_FORMAT = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/flac": "flac",
}


async def download_audio(state: CallState, config: RunnableConfig) -> dict:
    """Download audio from AudioLink URL into an in-memory bytes buffer.

    Returns ``audio_bytes`` and ``audio_format``.
    """
    audio_link = state["audio_link"]
    call_id = state.get("call_id") or "unknown"

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(audio_link)
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"Failed to download audio for call {call_id}: {e}", exc_info=True)
        raise

    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    audio_format = _MIME_TO_FORMAT.get(content_type)
    if audio_format is None:
        url_path = urlparse(audio_link).path
        ext = PurePosixPath(url_path).suffix.lower().lstrip(".")
        audio_format = ext or "wav"

    logger.info(f"Downloaded audio for call {call_id}: {audio_format} ({len(response.content)} bytes)")

    return {
        "audio_bytes": response.content,
        "audio_format": audio_format,
    }
