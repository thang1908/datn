"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["APP_ENV"] = "development"
os.environ["LITELLM_MODEL"] = "openai/gpt-4o-mini"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "conversation_db_test"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from src.main import app

    return TestClient(app)


@pytest.fixture
def sample_audio_bytes():
    """Create sample audio bytes for testing."""
    # WAV header for 1-second silence at 16kHz
    wav_header = bytes(
        [
            0x52,
            0x49,
            0x46,
            0x46,  # "RIFF"
            0x24,
            0xF0,
            0x00,
            0x00,  # File size
            0x57,
            0x41,
            0x56,
            0x45,  # "WAVE"
            0x66,
            0x6D,
            0x74,
            0x20,  # "fmt "
            0x10,
            0x00,
            0x00,
            0x00,  # Subchunk1 size
            0x01,
            0x00,  # Audio format (1 = PCM)
            0x01,
            0x00,  # Num channels
            0x80,
            0x3E,
            0x00,
            0x00,  # Sample rate (16000)
            0x00,
            0x7D,
            0x00,
            0x00,  # Byte rate
            0x02,
            0x00,  # Block align
            0x10,
            0x00,  # Bits per sample
            0x64,
            0x61,
            0x74,
            0x61,  # "data"
            0x00,
            0xF0,
            0x00,
            0x00,  # Subchunk2 size
        ]
    )
    # Add silence (zeros)
    silence = b"\x00" * (0xF000)
    return wav_header + silence


@pytest.fixture
def sample_base64_audio(sample_audio_bytes):
    """Create base64-encoded sample audio."""
    import base64

    return base64.b64encode(sample_audio_bytes).decode()
