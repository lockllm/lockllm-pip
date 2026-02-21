"""Tests for utility functions."""

import base64
import json
import time

import pytest

from lockllm.types.common import ProxyOptions
from lockllm.utils import (
    build_lockllm_headers,
    calculate_backoff,
    decode_detail_field,
    generate_request_id,
    get_all_proxy_urls,
    get_proxy_url,
    get_universal_proxy_url,
    parse_proxy_metadata,
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


class TestGetUniversalProxyUrl:
    """Tests for get_universal_proxy_url."""

    def test_returns_universal_url(self):
        """Test that it returns the universal proxy URL."""
        url = get_universal_proxy_url()
        assert url == "https://api.lockllm.com/v1/proxy"


class TestBuildLockLLMHeaders:
    """Tests for build_lockllm_headers."""

    def test_empty_options(self):
        """Test with all None options."""
        options = ProxyOptions()
        headers = build_lockllm_headers(options)
        assert headers == {}

    def test_all_options_set(self):
        """Test with all options set."""
        options = ProxyOptions(
            scan_mode="combined",
            scan_action="block",
            policy_action="allow_with_warning",
            abuse_action="block",
            route_action="auto",
            sensitivity="high",
            cache_response=True,
            cache_ttl=3600,
            chunk=True,
        )
        headers = build_lockllm_headers(options)

        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "allow_with_warning"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Route-Action"] == "auto"
        assert headers["X-LockLLM-Sensitivity"] == "high"
        assert headers["X-LockLLM-Cache-Response"] == "true"
        assert headers["X-LockLLM-Cache-TTL"] == "3600"
        assert headers["X-LockLLM-Chunk"] == "true"

    def test_partial_options(self):
        """Test with only some options set."""
        options = ProxyOptions(scan_action="block", route_action="auto")
        headers = build_lockllm_headers(options)

        assert len(headers) == 2
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Route-Action"] == "auto"

    def test_cache_response_false(self):
        """Test cache_response set to False."""
        options = ProxyOptions(cache_response=False)
        headers = build_lockllm_headers(options)

        assert headers["X-LockLLM-Cache-Response"] == "false"

    def test_chunk_false(self):
        """Test chunk set to False."""
        options = ProxyOptions(chunk=False)
        headers = build_lockllm_headers(options)

        assert headers["X-LockLLM-Chunk"] == "false"

    def test_pii_action_header(self):
        """Test pii_action produces X-LockLLM-PII-Action header."""
        options = ProxyOptions(pii_action="block")
        headers = build_lockllm_headers(options)

        assert headers["X-LockLLM-PII-Action"] == "block"

    def test_pii_action_strip(self):
        """Test pii_action=strip produces correct header."""
        options = ProxyOptions(pii_action="strip")
        headers = build_lockllm_headers(options)

        assert headers["X-LockLLM-PII-Action"] == "strip"


class TestDecodeDetailField:
    """Tests for decode_detail_field."""

    def test_decode_valid_json(self):
        """Test decoding valid base64-encoded JSON."""
        data = {"score": 95, "label": "unsafe"}
        encoded = base64.b64encode(json.dumps(data).encode()).decode()

        result = decode_detail_field(encoded)

        assert result == data
        assert result["score"] == 95

    def test_decode_invalid_base64(self):
        """Test decoding invalid base64 string."""
        result = decode_detail_field("not-valid-base64!!!")
        assert result is None

    def test_decode_invalid_json(self):
        """Test decoding valid base64 but invalid JSON."""
        encoded = base64.b64encode(b"not json").decode()
        result = decode_detail_field(encoded)
        assert result is None

    def test_decode_empty_object(self):
        """Test decoding empty object."""
        encoded = base64.b64encode(json.dumps({}).encode()).decode()
        result = decode_detail_field(encoded)
        assert result == {}


class TestParseProxyMetadata:
    """Tests for parse_proxy_metadata."""

    def test_minimal_headers(self):
        """Test parsing with minimal headers."""
        headers = {
            "x-request-id": "req_123",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.request_id == "req_123"
        assert metadata.scanned is True
        assert metadata.safe is True
        assert metadata.provider == "openai"
        assert metadata.scan_mode == "combined"
        assert metadata.credits_mode == "byok"

    def test_unsafe_response(self):
        """Test parsing unsafe response headers."""
        headers = {
            "x-request-id": "req_456",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-label": "1",
            "x-lockllm-provider": "anthropic",
            "x-lockllm-model": "claude-3",
            "x-lockllm-blocked": "true",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.safe is False
        assert metadata.label == 1
        assert metadata.model == "claude-3"
        assert metadata.blocked is True

    def test_label_invalid_value(self):
        """Test parsing invalid label value."""
        headers = {
            "x-request-id": "req_789",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-label": "invalid",
            "x-lockllm-provider": "openai",
        }
        metadata = parse_proxy_metadata(headers)

        # label should remain None since parsing failed
        assert metadata.label is None

    def test_policy_confidence(self):
        """Test parsing policy confidence."""
        headers = {
            "x-request-id": "req_abc",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-policy-confidence": "87.5",
        }
        metadata = parse_proxy_metadata(headers)
        assert metadata.policy_confidence == 87.5

    def test_scan_warning(self):
        """Test parsing scan warning headers."""
        headers = {
            "x-request-id": "req_warn",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-provider": "openai",
            "x-lockllm-scan-warning": "true",
            "x-lockllm-injection-score": "85.5",
            "x-lockllm-confidence": "92.0",
            "x-lockllm-scan-detail": "encoded_detail",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.scan_warning is not None
        assert metadata.scan_warning.injection_score == 85.5
        assert metadata.scan_warning.confidence == 92.0
        assert metadata.scan_warning.detail == "encoded_detail"

    def test_scan_warning_missing_scores(self):
        """Test parsing scan warning with missing optional scores."""
        headers = {
            "x-request-id": "req_warn2",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-provider": "openai",
            "x-lockllm-scan-warning": "true",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.scan_warning is not None
        assert metadata.scan_warning.injection_score == 0
        assert metadata.scan_warning.confidence == 0
        assert metadata.scan_warning.detail == ""

    def test_policy_warnings(self):
        """Test parsing policy warning headers."""
        headers = {
            "x-request-id": "req_policy",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-provider": "openai",
            "x-lockllm-policy-warnings": "true",
            "x-lockllm-warning-count": "3",
            "x-lockllm-policy-confidence": "90.0",
            "x-lockllm-warning-detail": "detail_encoded",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.policy_warnings is not None
        assert metadata.policy_warnings.count == 3
        assert metadata.policy_warnings.confidence == 90.0
        assert metadata.policy_warnings.detail == "detail_encoded"

    def test_policy_warnings_missing_values(self):
        """Test parsing policy warnings with missing optional values."""
        headers = {
            "x-request-id": "req_policy2",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-provider": "openai",
            "x-lockllm-policy-warnings": "true",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.policy_warnings is not None
        assert metadata.policy_warnings.count == 0
        assert metadata.policy_warnings.confidence == 0
        assert metadata.policy_warnings.detail == ""

    def test_abuse_detected(self):
        """Test parsing abuse detection headers."""
        headers = {
            "x-request-id": "req_abuse",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-provider": "openai",
            "x-lockllm-abuse-detected": "true",
            "x-lockllm-abuse-confidence": "88.0",
            "x-lockllm-abuse-types": "bot_generated,rapid_requests",
            "x-lockllm-abuse-detail": "abuse_detail_encoded",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.abuse_detected is not None
        assert metadata.abuse_detected.confidence == 88.0
        assert metadata.abuse_detected.types == "bot_generated,rapid_requests"
        assert metadata.abuse_detected.detail == "abuse_detail_encoded"

    def test_abuse_detected_missing_values(self):
        """Test parsing abuse detection with missing optional values."""
        headers = {
            "x-request-id": "req_abuse2",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "false",
            "x-lockllm-provider": "openai",
            "x-lockllm-abuse-detected": "true",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.abuse_detected is not None
        assert metadata.abuse_detected.confidence == 0
        assert metadata.abuse_detected.types == ""
        assert metadata.abuse_detected.detail == ""

    def test_routing_metadata(self):
        """Test parsing routing metadata headers."""
        headers = {
            "x-request-id": "req_route",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-route-enabled": "true",
            "x-lockllm-task-type": "Code Generation",
            "x-lockllm-complexity": "0.85",
            "x-lockllm-selected-model": "claude-3-sonnet",
            "x-lockllm-routing-reason": "High complexity code task",
            "x-lockllm-original-provider": "openai",
            "x-lockllm-original-model": "gpt-4",
            "x-lockllm-estimated-savings": "0.05",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.routing is not None
        assert metadata.routing.enabled is True
        assert metadata.routing.task_type == "Code Generation"
        assert metadata.routing.complexity == 0.85
        assert metadata.routing.selected_model == "claude-3-sonnet"
        assert metadata.routing.routing_reason == "High complexity code task"
        assert metadata.routing.original_provider == "openai"
        assert metadata.routing.original_model == "gpt-4"
        assert metadata.routing.estimated_savings == 0.05

    def test_routing_metadata_missing_values(self):
        """Test parsing routing metadata with missing optional values."""
        headers = {
            "x-request-id": "req_route2",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-route-enabled": "true",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.routing is not None
        assert metadata.routing.enabled is True
        assert metadata.routing.task_type == ""
        assert metadata.routing.complexity == 0
        assert metadata.routing.selected_model == ""

    def test_credit_tracking(self):
        """Test parsing credit tracking headers."""
        headers = {
            "x-request-id": "req_credits",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-credits-reserved": "0.05",
            "x-lockllm-routing-fee-reserved": "0.01",
            "x-lockllm-routing-fee-reason": "cost_savings",
            "x-lockllm-credits-deducted": "0.03",
            "x-lockllm-balance-after": "10.50",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.credits_reserved == 0.05
        assert metadata.routing_fee_reserved == 0.01
        assert metadata.routing_fee_reason == "cost_savings"
        assert metadata.credits_deducted == 0.03
        assert metadata.balance_after == 10.50

    def test_routing_cost_estimates(self):
        """Test parsing routing cost estimate headers."""
        headers = {
            "x-request-id": "req_cost",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-estimated-original-cost": "0.10",
            "x-lockllm-estimated-routed-cost": "0.03",
            "x-lockllm-estimated-input-tokens": "1000",
            "x-lockllm-estimated-output-tokens": "500",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.estimated_original_cost == 0.10
        assert metadata.estimated_routed_cost == 0.03
        assert metadata.estimated_input_tokens == 1000
        assert metadata.estimated_output_tokens == 500

    def test_cache_metadata(self):
        """Test parsing cache metadata headers."""
        headers = {
            "x-request-id": "req_cache",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-cache-status": "HIT",
            "x-lockllm-cache-age": "120",
            "x-lockllm-tokens-saved": "5000",
            "x-lockllm-cost-saved": "0.025",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.cache_status == "HIT"
        assert metadata.cache_age == 120
        assert metadata.tokens_saved == 5000
        assert metadata.cost_saved == 0.025

    def test_case_insensitive_headers(self):
        """Test that header lookup is case-insensitive."""
        headers = {
            "X-Request-Id": "req_case",
            "X-LockLLM-Scanned": "true",
            "X-LockLLM-Safe": "true",
            "X-LockLLM-Provider": "openai",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.request_id == "req_case"
        assert metadata.scanned is True
        assert metadata.safe is True

    def test_no_optional_fields(self):
        """Test that optional fields default correctly."""
        headers = {}
        metadata = parse_proxy_metadata(headers)

        assert metadata.request_id == ""
        assert metadata.scanned is False
        assert metadata.safe is False
        assert metadata.scan_warning is None
        assert metadata.policy_warnings is None
        assert metadata.abuse_detected is None
        assert metadata.routing is None
        assert metadata.credits_reserved is None
        assert metadata.credits_deducted is None
        assert metadata.cache_status is None

    def test_scan_mode_and_credits_mode(self):
        """Test parsing scan_mode and credits_mode headers."""
        headers = {
            "x-request-id": "req_modes",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-scan-mode": "normal",
            "x-lockllm-credits-mode": "lockllm_credits",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.scan_mode == "normal"
        assert metadata.credits_mode == "lockllm_credits"

    def test_sensitivity_header(self):
        """Test parsing sensitivity header."""
        headers = {
            "x-request-id": "req_sens",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-sensitivity": "high",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.sensitivity == "high"

    def test_pii_detected_headers(self):
        """Test parsing PII detection headers."""
        headers = {
            "x-request-id": "req_pii",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-pii-detected": "true",
            "x-lockllm-pii-types": "email,phone,ssn",
            "x-lockllm-pii-count": "5",
            "x-lockllm-pii-action": "strip",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.pii_detected is not None
        assert metadata.pii_detected.detected is True
        assert metadata.pii_detected.entity_types == "email,phone,ssn"
        assert metadata.pii_detected.entity_count == 5
        assert metadata.pii_detected.action == "strip"

    def test_pii_detected_false(self):
        """Test parsing PII detection with detected=false."""
        headers = {
            "x-request-id": "req_pii2",
            "x-lockllm-scanned": "true",
            "x-lockllm-safe": "true",
            "x-lockllm-provider": "openai",
            "x-lockllm-pii-detected": "false",
        }
        metadata = parse_proxy_metadata(headers)

        assert metadata.pii_detected is not None
        assert metadata.pii_detected.detected is False
        assert metadata.pii_detected.entity_types == ""
        assert metadata.pii_detected.entity_count == 0
        assert metadata.pii_detected.action == ""
