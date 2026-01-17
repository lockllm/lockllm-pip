"""Tests for type definitions."""

import pytest

from lockllm.types.common import LockLLMConfig, RequestOptions
from lockllm.types.providers import PROVIDER_BASE_URLS, ProviderName
from lockllm.types.scan import Debug, ScanRequest, ScanResponse, ScanResult, Usage


class TestLockLLMConfig:
    """Tests for LockLLMConfig."""

    def test_config_with_defaults(self):
        """Test configuration with default values."""
        config = LockLLMConfig(api_key="test_key")

        assert config.api_key == "test_key"
        assert config.base_url == "https://api.lockllm.com"
        assert config.timeout == 60.0
        assert config.max_retries == 3

    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = LockLLMConfig(
            api_key="test_key",
            base_url="https://custom.lockllm.com",
            timeout=30.0,
            max_retries=5,
        )

        assert config.api_key == "test_key"
        assert config.base_url == "https://custom.lockllm.com"
        assert config.timeout == 30.0
        assert config.max_retries == 5


class TestRequestOptions:
    """Tests for RequestOptions."""

    def test_request_options_defaults(self):
        """Test request options with defaults."""
        options = RequestOptions()

        assert options.headers is None
        assert options.timeout is None

    def test_request_options_with_values(self):
        """Test request options with values."""
        options = RequestOptions(
            headers={"X-Custom": "value"}, timeout=15.0
        )

        assert options.headers == {"X-Custom": "value"}
        assert options.timeout == 15.0


class TestProviders:
    """Tests for provider definitions."""

    def test_provider_base_urls_count(self):
        """Test that all 17 providers have URLs."""
        assert len(PROVIDER_BASE_URLS) == 17

    def test_provider_base_urls_format(self):
        """Test that all provider URLs are correctly formatted."""
        for provider, url in PROVIDER_BASE_URLS.items():
            assert url.startswith("https://api.lockllm.com/v1/proxy/")
            assert provider in url

    def test_all_providers_exist(self):
        """Test that all expected providers exist."""
        expected_providers = [
            "openai",
            "anthropic",
            "gemini",
            "cohere",
            "openrouter",
            "perplexity",
            "mistral",
            "groq",
            "deepseek",
            "together",
            "xai",
            "fireworks",
            "anyscale",
            "huggingface",
            "azure",
            "bedrock",
            "vertex-ai",
        ]

        for provider in expected_providers:
            assert provider in PROVIDER_BASE_URLS


class TestScanTypes:
    """Tests for scan-related types."""

    def test_scan_request(self):
        """Test ScanRequest creation."""
        request = ScanRequest(input="test prompt", sensitivity="high")

        assert request.input == "test prompt"
        assert request.sensitivity == "high"

    def test_scan_request_default_sensitivity(self):
        """Test ScanRequest with default sensitivity."""
        request = ScanRequest(input="test prompt")

        assert request.input == "test prompt"
        assert request.sensitivity == "medium"

    def test_usage(self):
        """Test Usage creation."""
        usage = Usage(requests=2, input_chars=100)

        assert usage.requests == 2
        assert usage.input_chars == 100

    def test_debug(self):
        """Test Debug creation."""
        debug = Debug(duration_ms=150, inference_ms=120, mode="single")

        assert debug.duration_ms == 150
        assert debug.inference_ms == 120
        assert debug.mode == "single"

    def test_scan_result(self):
        """Test ScanResult creation."""
        result = ScanResult(
            safe=True,
            label=0,
            confidence=95.5,
            injection=2.3,
            sensitivity="medium",
        )

        assert result.safe is True
        assert result.label == 0
        assert result.confidence == 95.5
        assert result.injection == 2.3
        assert result.sensitivity == "medium"

    def test_scan_response_without_debug(self):
        """Test ScanResponse without debug info."""
        usage = Usage(requests=1, input_chars=50)
        response = ScanResponse(
            safe=True,
            label=0,
            confidence=95.5,
            injection=2.3,
            sensitivity="medium",
            request_id="test_123",
            usage=usage,
        )

        assert response.safe is True
        assert response.request_id == "test_123"
        assert response.usage == usage
        assert response.debug is None

    def test_scan_response_with_debug(self):
        """Test ScanResponse with debug info."""
        usage = Usage(requests=1, input_chars=50)
        debug = Debug(duration_ms=150, inference_ms=120, mode="chunked")
        response = ScanResponse(
            safe=False,
            label=1,
            confidence=92.0,
            injection=88.5,
            sensitivity="high",
            request_id="test_456",
            usage=usage,
            debug=debug,
        )

        assert response.safe is False
        assert response.label == 1
        assert response.debug == debug
        assert response.debug.mode == "chunked"
