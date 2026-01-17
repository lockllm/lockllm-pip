"""Tests for utility functions."""

import time

import pytest

from lockllm.utils import (
    calculate_backoff,
    generate_request_id,
    get_all_proxy_urls,
    get_proxy_url,
    parse_retry_after,
)


class TestGenerateRequestId:
    """Tests for generate_request_id."""

    def test_generates_unique_ids(self):
        """Test that generated IDs are unique."""
        id1 = generate_request_id()
        id2 = generate_request_id()

        assert id1 != id2

    def test_generates_correct_length(self):
        """Test that generated IDs are 16 characters."""
        request_id = generate_request_id()

        assert len(request_id) == 16

    def test_generates_hex_string(self):
        """Test that generated IDs are hexadecimal."""
        request_id = generate_request_id()

        # Should be valid hex
        int(request_id, 16)  # Raises ValueError if not hex


class TestCalculateBackoff:
    """Tests for calculate_backoff."""

    def test_backoff_increases_exponentially(self):
        """Test that backoff increases exponentially."""
        backoff0 = calculate_backoff(0, base_delay=1000, max_delay=30000)
        backoff1 = calculate_backoff(1, base_delay=1000, max_delay=30000)
        backoff2 = calculate_backoff(2, base_delay=1000, max_delay=30000)

        # Should roughly double each time (with jitter)
        assert backoff0 < backoff1 < backoff2

    def test_backoff_respects_max_delay(self):
        """Test that backoff doesn't exceed max delay."""
        # Large attempt number should hit max
        backoff = calculate_backoff(10, base_delay=1000, max_delay=5000)

        # Should be around max_delay (5000) plus jitter (up to 500)
        assert backoff <= 5500

    def test_backoff_includes_jitter(self):
        """Test that backoff includes jitter."""
        # Generate multiple backoffs for same attempt
        backoffs = [calculate_backoff(0, base_delay=1000) for _ in range(10)]

        # Should have some variation due to jitter
        assert len(set(backoffs)) > 1

    def test_backoff_with_zero_attempt(self):
        """Test backoff with zero attempt."""
        backoff = calculate_backoff(0, base_delay=1000)

        # Should be base delay plus jitter (up to 100)
        assert 1000 <= backoff <= 1100

    def test_backoff_custom_parameters(self):
        """Test backoff with custom parameters."""
        backoff = calculate_backoff(2, base_delay=500, max_delay=2000)

        # 500 * 2^2 = 2000, plus jitter up to 200
        assert backoff <= 2200


class TestParseRetryAfter:
    """Tests for parse_retry_after."""

    def test_parse_seconds(self):
        """Test parsing retry-after as seconds."""
        result = parse_retry_after("5")

        assert result == 5000  # 5 seconds = 5000ms

    def test_parse_zero_seconds(self):
        """Test parsing zero seconds."""
        result = parse_retry_after("0")

        assert result == 0

    def test_parse_none(self):
        """Test parsing None."""
        result = parse_retry_after(None)

        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_retry_after("")

        assert result is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format."""
        result = parse_retry_after("invalid")

        # Should return None for invalid format
        assert result is None

    def test_parse_http_date(self):
        """Test parsing HTTP date format."""
        # HTTP date format
        result = parse_retry_after("Wed, 21 Oct 2025 07:28:00 GMT")

        # Should return some positive milliseconds or None
        assert result is None or result >= 0


class TestGetProxyUrl:
    """Tests for get_proxy_url."""

    def test_get_openai_proxy_url(self):
        """Test getting OpenAI proxy URL."""
        url = get_proxy_url("openai")

        assert url == "https://api.lockllm.com/v1/proxy/openai"

    def test_get_anthropic_proxy_url(self):
        """Test getting Anthropic proxy URL."""
        url = get_proxy_url("anthropic")

        assert url == "https://api.lockllm.com/v1/proxy/anthropic"

    def test_get_all_providers(self):
        """Test getting URLs for all providers."""
        providers = [
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

        for provider in providers:
            url = get_proxy_url(provider)  # type: ignore
            assert url.startswith("https://api.lockllm.com/v1/proxy/")
            assert provider in url


class TestGetAllProxyUrls:
    """Tests for get_all_proxy_urls."""

    def test_get_all_proxy_urls(self):
        """Test getting all proxy URLs."""
        urls = get_all_proxy_urls()

        assert len(urls) == 17
        assert "openai" in urls
        assert "anthropic" in urls

    def test_returns_copy(self):
        """Test that it returns a copy, not the original."""
        urls1 = get_all_proxy_urls()
        urls2 = get_all_proxy_urls()

        # Should be equal but not the same object
        assert urls1 == urls2
        assert urls1 is not urls2

    def test_all_urls_valid(self):
        """Test that all URLs are properly formatted."""
        urls = get_all_proxy_urls()

        for provider, url in urls.items():
            assert url.startswith("https://api.lockllm.com/v1/proxy/")
            assert provider in url
