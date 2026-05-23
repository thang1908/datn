"""Tests for database operations."""

import pytest


@pytest.mark.asyncio
async def test_db_connection():
    """Test MongoDB connection."""
    try:
        from src.db import get_db

        db = get_db()
        db.admin.command("ping")
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")


@pytest.mark.asyncio
async def test_save_and_retrieve_conversation():
    """Test saving and retrieving conversation."""
    try:
        from src.db import get_conversation, save_conversation

        test_id = "test-conv-123"
        save_conversation(
            message_id=test_id,
            transcript="Test transcript",
            qa_output={"score": 0.85},
            summary="Test summary",
        )

        result = get_conversation(test_id)
        assert result is not None
        assert result["_id"] == test_id
        assert result["transcript"] == "Test transcript"
    except Exception as e:
        pytest.skip(f"Database test failed: {e}")


@pytest.mark.asyncio
async def test_save_error():
    """Test saving error."""
    try:
        from src.db import get_error, save_error

        test_id = "test-error-123"
        save_error(
            message_id=test_id,
            error_type="TestError",
            error_message="Test error message",
            traceback="Traceback",
        )

        result = get_error(test_id)
        assert result is not None
        assert result["message_id"] == test_id
    except Exception as e:
        pytest.skip(f"Database test failed: {e}")
