"""Tests for synchronous HTTP client."""

from unittest.mock import Mock, patch

import pytest
import requests

from lockllm.errors import (
    AuthenticationError,
    LockLLMError,
    NetworkError,
    RateLimitError,
)
from lockllm.http_client import HttpClient


class TestHttpClient:
    """Tests for HttpClient."""

    def test_initialization(self, api_key):
        """Test client initialization."""
        client = HttpClient(
            base_url="https://api.lockllm.com",
            api_key=api_key,
            timeout=30.0,
            max_retries=5,
        )

        assert client.base_url == "https://api.lockllm.com"
        assert client.api_key == api_key
        assert client.timeout == 30.0
        assert client.max_retries == 5

    def test_initialization_strips_trailing_slash(self, api_key):
        """Test that trailing slash is stripped from base URL."""
        client = HttpClient(
            base_url="https://api.lockllm.com/",
            api_key=api_key,
        )

        assert client.base_url == "https://api.lockllm.com"

    @patch("requests.Session.request")
    def test_successful_post(self, mock_request, api_key, mock_scan_response):
        """Test successful POST request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = mock_scan_response
        mock_response.headers = {"X-Request-Id": "test_123"}
        mock_request.return_value = mock_response

        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        data, request_id = client.post("/v1/scan", body={"input": "test"})

        assert data == mock_scan_response
        assert request_id == "test_123"
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_successful_get(self, mock_request, api_key):
        """Test successful GET request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"X-Request-Id": "test_123"}
        mock_request.return_value = mock_response

        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        data, request_id = client.get("/v1/status")

        assert data == {"data": "test"}
        assert request_id == "test_123"

    @patch("requests.Session.request")
    def test_rate_limit_with_retry_after(self, mock_request, api_key):
        """Test rate limit error with Retry-After header."""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {"message": "Rate limit exceeded"}
        }
        mock_response.headers = {
            "X-Request-Id": "test_123",
            "Retry-After": "5",
        }
        mock_request.return_value = mock_response

        client = HttpClient(
            base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.post("/v1/scan", body={"input": "test"})

        error = exc_info.value
        assert error.retry_after == 5000  # 5 seconds = 5000ms

    @patch("requests.Session.request")
    @patch("time.sleep")
    def test_rate_limit_with_retry(
        self, mock_sleep, mock_request, api_key, mock_scan_response
    ):
        """Test rate limit with automatic retry."""
        # First call: rate limit, second call: success
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {
            "error": {"message": "Rate limit exceeded"}
        }
        rate_limit_response.headers = {
            "X-Request-Id": "test_123",
            "Retry-After": "1",
        }

        success_response = Mock()
        success_response.ok = True
        success_response.json.return_value = mock_scan_response
        success_response.headers = {"X-Request-Id": "test_456"}

        mock_request.side_effect = [rate_limit_response, success_response]

        client = HttpClient(
            base_url="https://api.lockllm.com", api_key=api_key, max_retries=1
        )

        data, request_id = client.post("/v1/scan", body={"input": "test"})

        assert data == mock_scan_response
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once()  # Should sleep before retry

    @patch("requests.Session.request")
    def test_authentication_error(self, mock_request, api_key):
        """Test authentication error."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error",
                "code": "unauthorized",
            }
        }
        mock_response.headers = {"X-Request-Id": "test_123"}
        mock_request.return_value = mock_response

        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        with pytest.raises(AuthenticationError) as exc_info:
            client.post("/v1/scan", body={"input": "test"})

        error = exc_info.value
        assert "Invalid API key" in error.message

    @patch("requests.Session.request")
    @patch("time.sleep")
    def test_network_error_with_retry(self, mock_sleep, mock_request, api_key):
        """Test network error with automatic retry."""
        # Simulate connection error
        mock_request.side_effect = requests.ConnectionError("Connection failed")

        client = HttpClient(
            base_url="https://api.lockllm.com", api_key=api_key, max_retries=2
        )

        with pytest.raises(NetworkError) as exc_info:
            client.post("/v1/scan", body={"input": "test"})

        error = exc_info.value
        assert "Network request failed" in error.message
        assert error.cause is not None
        # Should retry max_retries times, so total calls = max_retries + 1
        assert mock_request.call_count == 3

    @patch("requests.Session.request")
    def test_timeout_error(self, mock_request, api_key):
        """Test timeout error."""
        mock_request.side_effect = requests.Timeout("Request timeout")

        client = HttpClient(
            base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
        )

        with pytest.raises(NetworkError):
            client.post("/v1/scan", body={"input": "test"})

    @patch("requests.Session.request")
    def test_custom_headers(self, mock_request, api_key, mock_scan_response):
        """Test request with custom headers."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = mock_scan_response
        mock_response.headers = {"X-Request-Id": "test_123"}
        mock_request.return_value = mock_response

        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        custom_headers = {"X-Custom-Header": "custom-value"}
        client.post("/v1/scan", body={"input": "test"}, headers=custom_headers)

        # Verify custom header was included
        call_kwargs = mock_request.call_args[1]
        assert "X-Custom-Header" in call_kwargs["headers"]
        assert call_kwargs["headers"]["X-Custom-Header"] == "custom-value"

    @patch("requests.Session.request")
    def test_custom_timeout(self, mock_request, api_key, mock_scan_response):
        """Test request with custom timeout."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = mock_scan_response
        mock_response.headers = {"X-Request-Id": "test_123"}
        mock_request.return_value = mock_response

        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        client.post("/v1/scan", body={"input": "test"}, timeout=15.0)

        # Verify custom timeout was used
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["timeout"] == 15.0

    def test_context_manager(self, api_key):
        """Test using client as context manager."""
        with HttpClient(base_url="https://api.lockllm.com", api_key=api_key) as client:
            assert client is not None

    @patch("requests.Session.request")
    def test_error_without_json_body(self, mock_request, api_key):
        """Test error response without JSON body."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "Internal Server Error"
        mock_response.headers = {"X-Request-Id": "test_123"}
        mock_request.return_value = mock_response

        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        with pytest.raises(LockLLMError) as exc_info:
            client.post("/v1/scan", body={"input": "test"})

        error = exc_info.value
        assert "500" in error.message

    def test_close_method(self, api_key):
        """Test explicit close method."""
        client = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)

        # Should not raise any errors
        client.close()

        # Should be idempotent
        client.close()

    @patch("requests.Session.request")
    @patch("time.sleep")
    def test_rate_limit_max_retries_with_json_error(
        self, mock_sleep, mock_request, api_key
    ):
        """Test rate limit error when max retries exhausted and JSON parsing fails."""
        # Mock rate limit response with invalid JSON
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.headers = {
            "X-Request-Id": "test_123",
            "Retry-After": "5",
        }
        mock_request.return_value = mock_response

        client = HttpClient(
            base_url="https://api.lockllm.com", api_key=api_key, max_retries=0
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.post("/v1/scan", body={"input": "test"})

        error = exc_info.value
        assert error.retry_after == 5000  # Should still parse Retry-After header
