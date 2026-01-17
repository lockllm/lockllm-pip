"""Tests for synchronous scan client."""

from unittest.mock import Mock, patch

import pytest

from lockllm.http_client import HttpClient
from lockllm.scan import ScanClient
from lockllm.types.scan import ScanResponse


class TestScanClient:
    """Tests for ScanClient."""

    def test_initialization(self, api_key):
        """Test scan client initialization."""
        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        assert scan_client._http == http

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_success(self, mock_post, api_key, mock_scan_response):
        """Test successful scan."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(input="test prompt", sensitivity="medium")

        assert isinstance(result, ScanResponse)
        assert result.safe is True
        assert result.confidence == 95
        assert result.injection == 2
        assert result.request_id == "test_request_123"
        assert result.usage.requests == 1
        assert result.usage.input_chars == 25

        # Verify HTTP client was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/v1/scan"
        assert call_args[1]["body"]["input"] == "test prompt"
        assert call_args[1]["body"]["sensitivity"] == "medium"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_with_debug_info(self, mock_post, api_key, mock_unsafe_scan_response):
        """Test scan with debug information."""
        mock_post.return_value = (mock_unsafe_scan_response, "test_request_456")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(input="malicious prompt", sensitivity="high")

        assert isinstance(result, ScanResponse)
        assert result.safe is False
        assert result.label == 1
        assert result.injection == 87
        assert result.debug is not None
        assert result.debug.duration_ms == 150
        assert result.debug.inference_ms == 120
        assert result.debug.mode == "single"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_with_custom_options(self, mock_post, api_key, mock_scan_response):
        """Test scan with custom options."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(
            input="test",
            sensitivity="low",
            headers={"X-Custom": "value"},
            timeout=15.0,
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["headers"] == {"X-Custom": "value"}
        assert call_args[1]["timeout"] == 15.0

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_default_sensitivity(self, mock_post, api_key, mock_scan_response):
        """Test scan with default sensitivity."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(input="test prompt")

        call_args = mock_post.call_args
        assert call_args[1]["body"]["sensitivity"] == "medium"
