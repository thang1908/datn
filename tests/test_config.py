"""Tests for configuration."""

from src.core.config import settings


def test_settings_loaded():
    """Test that settings are properly loaded."""
    assert settings.app_name == "CS Agent QA API"
    assert settings.app_version == "1.0.0"
    assert settings.litellm_model is not None


def test_kafka_broker_list():
    """Test Kafka broker list parsing."""
    brokers = settings.get_kafka_broker_list()
    assert isinstance(brokers, list)
    assert len(brokers) > 0


def test_environment_helpers():
    """Test environment check methods."""
    assert settings.is_development or settings.is_production


def test_mongodb_settings():
    """Test MongoDB settings."""
    assert settings.mongodb_uri is not None
    assert settings.mongodb_db_name is not None
