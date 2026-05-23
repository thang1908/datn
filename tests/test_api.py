"""Tests for FastAPI routes."""


def test_health_check(test_client):
    """Test basic health check."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"





def test_connections_status(test_client):
    """Test connections endpoint."""
    response = test_client.get("/connections")
    assert response.status_code == 200
    data = response.json()
    assert "kafka" in data
    assert "mongodb" in data
    assert "litellm" in data


def test_kafka_topics(test_client):
    """Test Kafka topics listing."""
    response = test_client.get("/kafka/topics")
    assert response.status_code in [200, 503]  # May fail if Kafka not available
    if response.status_code == 200:
        data = response.json()
        assert "topics" in data


def test_conversations_list_empty(test_client):
    """Test conversations list endpoint."""
    response = test_client.get("/conversations")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "limit" in data
    assert "results" in data


def test_get_nonexistent_conversation(test_client):
    """Test retrieving non-existent conversation."""
    response = test_client.get("/conversations/nonexistent-id")
    assert response.status_code == 404
