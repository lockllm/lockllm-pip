"""Tests for main LockLLM client."""

from unittest.mock import Mock, patch

import pytest

from lockllm.client import LockLLM
from lockllm.errors import ConfigurationError
from lockllm.types.scan import ScanResponse


class TestLockLLM:
    """Tests for LockLLM main client."""

    def test_initialization_with_api_key(self, api_key):
        """Test initialization with API key."""
        client = LockLLM(api_key=api_key)

        assert client.config.api_key == api_key
        assert client.config.base_url == "https://api.lockllm.com"
        assert client.config.timeout == 60.0
        assert client.config.max_retries == 3

    def test_initialization_with_custom_config(self, api_key):
        """Test initialization with custom configuration."""
        client = LockLLM(
            api_key=api_key,
            base_url="https://custom.lockllm.com",
            timeout=30.0,
            max_retries=5,
        )

        assert client.config.base_url == "https://custom.lockllm.com"
        assert client.config.timeout == 30.0
        assert client.config.max_retries == 5

    def test_initialization_without_api_key(self):
        """Test that initialization without API key raises error."""
        with pytest.raises(ConfigurationError) as exc_info:
            LockLLM(api_key="")

        assert "API key is required" in str(exc_info.value)

    def test_initialization_with_whitespace_api_key(self):
        """Test that initialization with whitespace API key raises error."""
        with pytest.raises(ConfigurationError):
            LockLLM(api_key="   ")

    @patch("lockllm.scan.ScanClient.scan")
    def test_scan_delegates_to_scan_client(self, mock_scan, api_key, mock_scan_response):
        """Test that scan method delegates to scan client."""
        # Create mock scan response
        from lockllm.types.scan import Usage

        usage = Usage(requests=1, input_chars=25)
        scan_response = ScanResponse(
            safe=True,
            label=0,
            confidence=95.5,
            injection=2.3,
            sensitivity="medium",
            request_id="test_123",
            usage=usage,
        )
        mock_scan.return_value = scan_response

        client = LockLLM(api_key=api_key)
        result = client.scan(input="test prompt", sensitivity="high")

        assert result == scan_response
        mock_scan.assert_called_once_with(
            input="test prompt", sensitivity="high"
        )

    def test_config_property(self, api_key):
        """Test that config property returns configuration."""
        client = LockLLM(api_key=api_key)
        config = client.config

        assert config.api_key == api_key
        assert config.base_url == "https://api.lockllm.com"

    def test_context_manager(self, api_key):
        """Test using client as context manager."""
        with LockLLM(api_key=api_key) as client:
            assert client is not None
            assert client.config.api_key == api_key

    @patch("lockllm.http_client.HttpClient.close")
    def test_close_method(self, mock_close, api_key):
        """Test that close method closes HTTP client."""
        client = LockLLM(api_key=api_key)
        client.close()

        mock_close.assert_called_once()

    @patch("lockllm.http_client.HttpClient.close")
    def test_context_manager_closes(self, mock_close, api_key):
        """Test that context manager closes client."""
        with LockLLM(api_key=api_key) as client:
            pass

        mock_close.assert_called_once()

    @patch("lockllm.scan.ScanClient.scan")
    def test_scan_with_options(self, mock_scan, api_key):
        """Test scan with additional options."""
        from lockllm.types.scan import Usage

        usage = Usage(requests=1, input_chars=25)
        scan_response = ScanResponse(
            safe=True,
            label=0,
            confidence=95.5,
            injection=2.3,
            sensitivity="low",
            request_id="test_123",
            usage=usage,
        )
        mock_scan.return_value = scan_response

        client = LockLLM(api_key=api_key)
        result = client.scan(
            input="test",
            sensitivity="low",
            headers={"X-Custom": "value"},
            timeout=15.0,
        )

        mock_scan.assert_called_once_with(
            input="test",
            sensitivity="low",
            headers={"X-Custom": "value"},
            timeout=15.0,
        )
