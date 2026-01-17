"""Tests for asynchronous HTTP client."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from lockllm.async_http_client import AsyncHttpClient
from lockllm.errors import (
    AuthenticationError,
    LockLLMError,
    NetworkError,
    RateLimitError,
)


class TestAsyncHttpClient:
    """Tests for AsyncHttpClient."""

    def test_initialization(self, api_key):
        """Test client initialization."""
        client = AsyncHttpClient(
            base_url="https://api.lockllm.com",
            api_key=api_key,
            timeout=30.0,
            max_retries=5,
        )

        assert client.base_url == "https://api.lockllm.com"
        assert client.api_key == api_key
        assert client.timeout == 30.0
        assert client.max_retries == 5

    @pytest.mark.asyncio
    async def test_successful_post(self, api_key, mock_scan_response):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = mock_scan_response
        mock_response.headers = {"x-request-id": "test_123"}

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key
            )

            data, request_id = await client.post("/v1/scan", body={"input": "test"})

            assert data == mock_scan_response
            assert request_id == "test_123"

    @pytest.mark.asyncio
    async def test_successful_get(self, api_key):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"x-request-id": "test_123"}

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key
            )

            data, request_id = await client.get("/v1/status")

            assert data == {"data": "test"}
            assert request_id == "test_123"

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, api_key):
        """Test rate limit error."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {"message": "Rate limit exceeded"}
        }
        mock_response.headers = {
            "x-request-id": "test_123",
            "retry-after": "5",
        }

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
            )

            with pytest.raises(RateLimitError) as exc_info:
                await client.post("/v1/scan", body={"input": "test"})

            error = exc_info.value
            assert error.retry_after == 5000

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_rate_limit_with_retry(
        self, mock_sleep, api_key, mock_scan_response
    ):
        """Test rate limit with automatic retry."""
        # First call: rate limit, second call: success
        rate_limit_response = Mock()
        rate_limit_response.is_success = False
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {
            "error": {"message": "Rate limit exceeded"}
        }
        rate_limit_response.headers = {
            "x-request-id": "test_123",
            "retry-after": "1",
        }

        success_response = Mock()
        success_response.is_success = True
        success_response.json.return_value = mock_scan_response
        success_response.headers = {"x-request-id": "test_456"}

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = [rate_limit_response, success_response]

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key, max_retries=1
            )

            data, request_id = await client.post("/v1/scan", body={"input": "test"})

            assert data == mock_scan_response
            assert mock_request.call_count == 2
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_error(self, api_key):
        """Test authentication error."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error",
                "code": "unauthorized",
            }
        }
        mock_response.headers = {"x-request-id": "test_123"}

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key
            )

            with pytest.raises(AuthenticationError):
                await client.post("/v1/scan", body={"input": "test"})

    @pytest.mark.asyncio
    async def test_network_error(self, api_key):
        """Test network error."""
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection failed")

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
            )

            with pytest.raises(NetworkError):
                await client.post("/v1/scan", body={"input": "test"})

    @pytest.mark.asyncio
    async def test_timeout_error(self, api_key):
        """Test timeout error."""
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Request timeout")

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
            )

            with pytest.raises(NetworkError):
                await client.post("/v1/scan", body={"input": "test"})

    @pytest.mark.asyncio
    async def test_custom_headers(self, api_key, mock_scan_response):
        """Test request with custom headers."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = mock_scan_response
        mock_response.headers = {"x-request-id": "test_123"}

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key
            )

            custom_headers = {"X-Custom-Header": "custom-value"}
            await client.post("/v1/scan", body={"input": "test"}, headers=custom_headers)

            call_kwargs = mock_request.call_args[1]
            assert "X-Custom-Header" in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_context_manager(self, api_key):
        """Test using client as async context manager."""
        async with AsyncHttpClient(
            base_url="https://api.lockllm.com", api_key=api_key
        ) as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_close(self, api_key):
        """Test closing the client."""
        client = AsyncHttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        # Access client to create it
        _ = client.client

        # Close should work without error
        await client.close()

        # After close, client should be None
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_without_client_created(self, api_key):
        """Test closing when client was never created."""
        client = AsyncHttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        # Close without ever accessing client
        await client.close()

        # Should not raise error
        assert client._client is None

    @pytest.mark.asyncio
    async def test_error_without_json_body(self, api_key):
        """Test error response without JSON body."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "Internal Server Error"
        mock_response.headers = {"x-request-id": "test_123"}

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key
            )

            with pytest.raises(LockLLMError) as exc_info:
                await client.post("/v1/scan", body={"input": "test"})

            error = exc_info.value
            assert "500" in error.message

    @pytest.mark.asyncio
    async def test_rate_limit_max_retries_with_json_error(self, api_key):
        """Test rate limit error when max retries exhausted and JSON parsing fails."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 429
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.headers = {
            "x-request-id": "test_123",
            "retry-after": "5",
        }

        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
            )

            with pytest.raises(RateLimitError) as exc_info:
                await client.post("/v1/scan", body={"input": "test"})

            error = exc_info.value
            assert error.retry_after == 5000

    @pytest.mark.asyncio
    async def test_network_error_with_retry_and_backoff(self, api_key):
        """Test network error with retry and backoff."""
        with patch.object(
            httpx.AsyncClient, "request", new_callable=AsyncMock
        ) as mock_request:
            # Fail twice, then succeed
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.json.return_value = {"safe": True, "label": 0, "confidence": 95, "injection": 2, "sensitivity": "medium", "request_id": "req_123", "usage": {"requests": 1, "input_chars": 10}}
            mock_response.headers = {"x-request-id": "test_123"}

            mock_request.side_effect = [
                httpx.ConnectError("Connection failed"),
                httpx.ConnectError("Connection failed"),
                mock_response,
            ]

            client = AsyncHttpClient(
                base_url="https://api.lockllm.com", api_key=api_key, max_retries=2
            )

            # Should eventually succeed after retries
            data, request_id = await client.post("/v1/scan", body={"input": "test"})

            assert data["safe"] is True
            assert mock_request.call_count == 3
