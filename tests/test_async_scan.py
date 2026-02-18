"""Tests for asynchronous scan client."""

from unittest.mock import AsyncMock, Mock

import pytest

from lockllm.async_scan import AsyncScanClient
from lockllm.errors import PromptInjectionError
from lockllm.types import ScanRequest
from lockllm.types.scan import ScanOptions


class TestAsyncScanClient:
    """Tests for AsyncScanClient."""

    @pytest.mark.asyncio
    async def test_initialization(self, api_key):
        """Test client initialization."""
        from lockllm.async_http_client import AsyncHttpClient

        http_client = AsyncHttpClient(
            base_url="https://api.lockllm.com", api_key=api_key
        )
        client = AsyncScanClient(http=http_client)

        assert client._http is not None

    @pytest.mark.asyncio
    async def test_scan_basic(self, api_key, mock_scan_response):
        """Test basic scan operation."""
        # Create mock HTTP client
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=(mock_scan_response, "req_123"))

        client = AsyncScanClient(http=mock_http_client)

        result = await client.scan(
            input="Test prompt",
            sensitivity="medium",
        )

        assert result.safe == mock_scan_response["safe"]
        assert result.label == mock_scan_response["label"]
        assert result.confidence == mock_scan_response["confidence"]
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_with_all_params(self, api_key, mock_scan_response):
        """Test scan with all parameters."""
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=(mock_scan_response, "req_123"))

        client = AsyncScanClient(http=mock_http_client)

        result = await client.scan(
            input="Test prompt",
            sensitivity="high",
            output="all",
            explain=True,
            request_id="custom_req_id",
            headers={"X-Custom": "value"},
            timeout=30.0,
        )

        assert result.safe == mock_scan_response["safe"]
        call_kwargs = mock_http_client.post.call_args[1]
        assert call_kwargs["timeout"] == 30.0
        assert "X-Custom" in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_scan_with_debug(self, api_key):
        """Test scan with debug information."""
        mock_http_client = AsyncMock()
        response_with_debug = {
            "safe": True,
            "label": 0,
            "confidence": 98,
            "injection": 2,
            "sensitivity": "medium",
            "request_id": "req_123",
            "usage": {"requests": 1, "input_chars": 11},
            "debug": {
                "duration_ms": 50,
                "inference_ms": 30,
                "mode": "single",
            },
        }
        mock_http_client.post = AsyncMock(
            return_value=(response_with_debug, "req_123")
        )

        client = AsyncScanClient(http=mock_http_client)

        result = await client.scan(input="Test prompt", explain=True)

        assert result.debug is not None
        assert result.debug.duration_ms == 50
        assert result.debug.inference_ms == 30
        assert result.debug.mode == "single"

    @pytest.mark.asyncio
    async def test_scan_with_scan_options(self, mock_scan_response):
        """Test async scan with ScanOptions object."""
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=(mock_scan_response, "req_123"))

        client = AsyncScanClient(http=mock_http_client)

        opts = ScanOptions(
            scan_mode="combined",
            scan_action="block",
            policy_action="allow_with_warning",
            abuse_action="block",
            chunk=True,
        )
        result = await client.scan(input="test", scan_options=opts)

        call_args = mock_http_client.post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "allow_with_warning"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Chunk"] == "true"

    @pytest.mark.asyncio
    async def test_scan_kwargs_override_scan_options(self, mock_scan_response):
        """Test that individual kwargs take precedence over ScanOptions in async."""
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=(mock_scan_response, "req_123"))

        client = AsyncScanClient(http=mock_http_client)

        opts = ScanOptions(
            scan_mode="normal",
            scan_action="allow_with_warning",
            policy_action="allow_with_warning",
            abuse_action="allow_with_warning",
            chunk=False,
        )
        result = await client.scan(
            input="test",
            scan_options=opts,
            scan_mode="combined",
            scan_action="block",
            policy_action="block",
            abuse_action="block",
            chunk=True,
        )

        call_args = mock_http_client.post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "block"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Chunk"] == "true"

    @pytest.mark.asyncio
    async def test_scan_with_all_header_options(self, mock_scan_response):
        """Test async scan with all header-producing options."""
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=(mock_scan_response, "req_123"))

        client = AsyncScanClient(http=mock_http_client)

        result = await client.scan(
            input="test",
            scan_mode="policy_only",
            scan_action="block",
            policy_action="allow_with_warning",
            abuse_action="block",
            chunk=False,
            sensitivity="low",
        )

        call_args = mock_http_client.post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-LockLLM-Scan-Mode"] == "policy_only"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "allow_with_warning"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Chunk"] == "false"
        assert headers["X-LockLLM-Sensitivity"] == "low"
