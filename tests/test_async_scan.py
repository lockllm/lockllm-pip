"""Tests for asynchronous scan client."""

from unittest.mock import AsyncMock, Mock

import pytest

from lockllm.async_scan import AsyncScanClient
from lockllm.errors import PromptInjectionError
from lockllm.types import ScanRequest


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
