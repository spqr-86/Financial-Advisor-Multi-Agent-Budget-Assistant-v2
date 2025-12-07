"""Tests for HTTP client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import ClientError, ClientTimeout

from src.core.http_client import ServiceClient
from src.core.exceptions import ServiceUnavailableError


@pytest.mark.asyncio
async def test_service_client_init():
    """Test ServiceClient initialization."""
    client = ServiceClient("http://localhost:8080", timeout=10, max_retries=5)
    assert client.base_url == "http://localhost:8080"
    assert client.timeout.total == 10
    assert client.max_retries == 5
    assert client._session is None


@pytest.mark.asyncio
async def test_service_client_get_session():
    """Test session creation."""
    client = ServiceClient("http://localhost:8080")
    session = await client._get_session()
    assert session is not None
    assert not session.closed
    await client.close()


@pytest.mark.asyncio
async def test_service_client_close():
    """Test session cleanup."""
    client = ServiceClient("http://localhost:8080")
    await client._get_session()
    assert client._session is not None
    await client.close()
    assert client._session is None


@pytest.mark.asyncio
async def test_service_client_get_success():
    """Test successful GET request."""
    client = ServiceClient("http://localhost:8080")

    with patch.object(client, "_get_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})
        mock_response.raise_for_status = Mock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_sess = AsyncMock()
        mock_sess.request = Mock(return_value=mock_response)
        mock_session.return_value = mock_sess

        result = await client.get("/test")
        assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_service_client_post_success():
    """Test successful POST request."""
    client = ServiceClient("http://localhost:8080")

    with patch.object(client, "_get_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"posted": "data"})
        mock_response.raise_for_status = Mock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_sess = AsyncMock()
        mock_sess.request = Mock(return_value=mock_response)
        mock_session.return_value = mock_sess

        result = await client.post("/test", json={"key": "value"})
        assert result == {"posted": "data"}


@pytest.mark.asyncio
async def test_service_client_retry_on_error():
    """Test retry logic on client error."""
    client = ServiceClient("http://localhost:8080", max_retries=3)

    with patch.object(client, "_get_session") as mock_session:
        mock_sess = AsyncMock()
        mock_sess.request = Mock(side_effect=ClientError("Connection error"))
        mock_session.return_value = mock_sess

        with pytest.raises(ServiceUnavailableError) as exc_info:
            await client.get("/test")

        assert "after 3 attempts" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_client_500_error():
    """Test handling of 500 server error."""
    client = ServiceClient("http://localhost:8080", max_retries=2)

    with patch.object(client, "_get_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_sess = AsyncMock()
        mock_sess.request = Mock(return_value=mock_response)
        mock_session.return_value = mock_sess

        with pytest.raises(ServiceUnavailableError):
            await client.get("/test")


@pytest.mark.asyncio
async def test_service_client_health_check_success():
    """Test successful health check."""
    client = ServiceClient("http://localhost:8080")

    with patch.object(client, "get") as mock_get:
        mock_get.return_value = {"status": "healthy"}
        result = await client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_service_client_health_check_failure():
    """Test failed health check."""
    client = ServiceClient("http://localhost:8080")

    with patch.object(client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection failed")
        result = await client.health_check()
        assert result is False


@pytest.mark.asyncio
async def test_service_client_health_check_wrong_status():
    """Test health check with wrong status."""
    client = ServiceClient("http://localhost:8080")

    with patch.object(client, "get") as mock_get:
        mock_get.return_value = {"status": "degraded"}
        result = await client.health_check()
        assert result is False
