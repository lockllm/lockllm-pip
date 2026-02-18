"""Tests for async LockLLM client."""

from unittest.mock import AsyncMock, patch

import pytest

from lockllm.async_client import AsyncLockLLM
from lockllm.errors import ConfigurationError
from lockllm.types.scan import ScanResponse, Usage


class TestAsyncLockLLM:
    """Tests for AsyncLockLLM main client."""

    def test_initialization_with_api_key(self, api_key):
        """Test initialization with API key."""
        client = AsyncLockLLM(api_key=api_key)

        assert client.config.api_key == api_key
        assert client.config.base_url == "https://api.lockllm.com"

    def test_initialization_without_api_key(self):
        """Test that initialization without API key raises error."""
        with pytest.raises(ConfigurationError):
            AsyncLockLLM(api_key="")

    @pytest.mark.asyncio
    @patch("lockllm.async_scan.AsyncScanClient.scan", new_callable=AsyncMock)
    async def test_scan_delegates_to_scan_client(
        self, mock_scan, api_key, mock_scan_response
    ):
        """Test that scan method delegates to scan client."""
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

        client = AsyncLockLLM(api_key=api_key)
        result = await client.scan(input="test prompt", sensitivity="high")

        assert result == scan_response
        mock_scan.assert_called_once_with(
            input="test prompt",
            sensitivity="high",
            scan_mode=None,
            scan_action=None,
            policy_action=None,
            abuse_action=None,
            chunk=None,
            scan_options=None,
        )

    @pytest.mark.asyncio
    async def test_context_manager(self, api_key):
        """Test using client as async context manager."""
        async with AsyncLockLLM(api_key=api_key) as client:
            assert client is not None
            assert client.config.api_key == api_key

    @pytest.mark.asyncio
    @patch("lockllm.async_http_client.AsyncHttpClient.close", new_callable=AsyncMock)
    async def test_close_method(self, mock_close, api_key):
        """Test that close method closes HTTP client."""
        client = AsyncLockLLM(api_key=api_key)
        await client.close()

        mock_close.assert_called_once()

    @pytest.mark.asyncio
    @patch("lockllm.async_http_client.AsyncHttpClient.close", new_callable=AsyncMock)
    async def test_context_manager_closes(self, mock_close, api_key):
        """Test that context manager closes client."""
        async with AsyncLockLLM(api_key=api_key) as client:
            pass

        mock_close.assert_called_once()
