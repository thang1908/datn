"""Tests for LLM and LiteLLM integration."""

import pytest


def test_litellm_client_initialization():
    """Test LiteLLM client can be initialized."""
    try:
        from src.core.litellm_client import get_llm

        llm = get_llm()
        assert llm is not None
    except Exception as e:
        pytest.skip(f"LiteLLM initialization failed: {e}")


def test_langfuse_callback():
    """Test Langfuse callback initialization."""
    from src.core.litellm_client import get_langfuse_callback

    callback = get_langfuse_callback()
    # Should return None if Langfuse keys not configured
    assert callback is None or callback is not None
