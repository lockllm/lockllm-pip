"""Tests for error handling."""

import pytest

from lockllm.errors import (
    AuthenticationError,
    ConfigurationError,
    LockLLMError,
    NetworkError,
    PromptInjectionError,
    RateLimitError,
    UpstreamError,
    parse_error,
)
from lockllm.types.scan import ScanResult


class TestLockLLMError:
    """Tests for base LockLLMError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = LockLLMError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.type == "lockllm_error"
        assert error.code is None
        assert error.status is None
        assert error.request_id is None

    def test_error_with_all_params(self):
        """Test error with all parameters."""
        error = LockLLMError(
            message="Test error",
            error_type="test_type",
            code="test_code",
            status=400,
            request_id="req_123",
        )

        assert error.message == "Test error"
        assert error.type == "test_type"
        assert error.code == "test_code"
        assert error.status == 400
        assert error.request_id == "req_123"

    def test_error_string_with_code(self):
        """Test error string representation with code."""
        error = LockLLMError("Test error", code="test_code")
        assert "(code: test_code)" in str(error)

    def test_error_string_with_request_id(self):
        """Test error string representation with request ID."""
        error = LockLLMError("Test error", request_id="req_123")
        assert "[request_id: req_123]" in str(error)


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_authentication_error(self):
        """Test authentication error creation."""
        error = AuthenticationError("Invalid API key", request_id="req_123")

        assert error.message == "Invalid API key"
        assert error.type == "authentication_error"
        assert error.code == "unauthorized"
        assert error.status == 401
        assert error.request_id == "req_123"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_rate_limit_error_without_retry_after(self):
        """Test rate limit error without retry_after."""
        error = RateLimitError("Rate limit exceeded", request_id="req_123")

        assert error.message == "Rate limit exceeded"
        assert error.type == "rate_limit_error"
        assert error.code == "rate_limited"
        assert error.status == 429
        assert error.retry_after is None

    def test_rate_limit_error_with_retry_after(self):
        """Test rate limit error with retry_after."""
        error = RateLimitError(
            "Rate limit exceeded", retry_after=5000, request_id="req_123"
        )

        assert error.retry_after == 5000


class TestPromptInjectionError:
    """Tests for PromptInjectionError."""

    def test_prompt_injection_error(self):
        """Test prompt injection error creation."""
        scan_result = ScanResult(
            safe=False,
            label=1,
            confidence=95.0,
            injection=90.5,
            sensitivity="high",
        )

        error = PromptInjectionError(
            "Injection detected", scan_result=scan_result, request_id="req_123"
        )

        assert error.message == "Injection detected"
        assert error.type == "lockllm_security_error"
        assert error.code == "prompt_injection_detected"
        assert error.status == 400
        assert error.scan_result == scan_result
        assert error.scan_result.injection == 90.5


class TestUpstreamError:
    """Tests for UpstreamError."""

    def test_upstream_error_basic(self):
        """Test basic upstream error."""
        error = UpstreamError("Provider error", request_id="req_123")

        assert error.message == "Provider error"
        assert error.type == "upstream_error"
        assert error.code == "provider_error"
        assert error.status == 502
        assert error.provider is None
        assert error.upstream_status is None

    def test_upstream_error_with_details(self):
        """Test upstream error with provider details."""
        error = UpstreamError(
            "OpenAI error",
            provider="openai",
            upstream_status=503,
            request_id="req_123",
        )

        assert error.provider == "openai"
        assert error.upstream_status == 503


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error(self):
        """Test configuration error creation."""
        error = ConfigurationError("Invalid configuration")

        assert error.message == "Invalid configuration"
        assert error.type == "configuration_error"
        assert error.code == "invalid_config"
        assert error.status == 400


class TestNetworkError:
    """Tests for NetworkError."""

    def test_network_error_without_cause(self):
        """Test network error without cause."""
        error = NetworkError("Connection failed", request_id="req_123")

        assert error.message == "Connection failed"
        assert error.type == "network_error"
        assert error.code == "connection_failed"
        assert error.status == 0
        assert error.cause is None

    def test_network_error_with_cause(self):
        """Test network error with cause."""
        cause = Exception("Timeout")
        error = NetworkError("Connection failed", cause=cause, request_id="req_123")

        assert error.cause == cause


class TestParseError:
    """Tests for error parsing."""

    def test_parse_empty_error(self):
        """Test parsing empty error response."""
        error = parse_error({}, request_id="req_123")

        assert isinstance(error, LockLLMError)
        assert "Unknown error" in error.message

    def test_parse_authentication_error(self):
        """Test parsing authentication error."""
        response = {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error",
                "code": "unauthorized",
            }
        }

        error = parse_error(response, request_id="req_123")

        assert isinstance(error, AuthenticationError)
        assert error.message == "Invalid API key"

    def test_parse_rate_limit_error(self):
        """Test parsing rate limit error."""
        response = {
            "error": {
                "message": "Too many requests",
                "type": "rate_limit_error",
                "code": "rate_limited",
            }
        }

        error = parse_error(response, request_id="req_123")

        assert isinstance(error, RateLimitError)
        assert error.message == "Too many requests"

    def test_parse_prompt_injection_error(self):
        """Test parsing prompt injection error."""
        response = {
            "error": {
                "message": "Malicious input detected",
                "type": "lockllm_security_error",
                "code": "prompt_injection_detected",
                "request_id": "req_789",
                "scan_result": {
                    "safe": False,
                    "label": 1,
                    "confidence": 95.0,
                    "injection": 90.5,
                    "sensitivity": "high",
                },
            }
        }

        error = parse_error(response)

        assert isinstance(error, PromptInjectionError)
        assert error.message == "Malicious input detected"
        assert error.scan_result.injection == 90.5
        assert error.request_id == "req_789"

    def test_parse_upstream_error(self):
        """Test parsing upstream error."""
        response = {
            "error": {
                "message": "Provider failed",
                "type": "upstream_error",
                "code": "provider_error",
            }
        }

        error = parse_error(response, request_id="req_123")

        assert isinstance(error, UpstreamError)
        assert error.message == "Provider failed"

    def test_parse_configuration_error(self):
        """Test parsing configuration error."""
        response = {
            "error": {
                "message": "No upstream key",
                "type": "configuration_error",
                "code": "no_upstream_key",
            }
        }

        error = parse_error(response, request_id="req_123")

        assert isinstance(error, ConfigurationError)
        assert error.message == "No upstream key"

    def test_parse_generic_error(self):
        """Test parsing generic error."""
        response = {
            "error": {
                "message": "Something went wrong",
                "type": "unknown_type",
                "code": "unknown_code",
            }
        }

        error = parse_error(response, request_id="req_123")

        assert isinstance(error, LockLLMError)
        assert error.message == "Something went wrong"
        assert error.type == "unknown_type"
        assert error.code == "unknown_code"

    def test_parse_error_by_code(self):
        """Test parsing errors by code when type is missing."""
        # Authentication by code
        response = {"error": {"message": "Auth failed", "code": "unauthorized"}}
        error = parse_error(response)
        assert isinstance(error, AuthenticationError)

        # Rate limit by code
        response = {"error": {"message": "Too fast", "code": "rate_limited"}}
        error = parse_error(response)
        assert isinstance(error, RateLimitError)

        # Upstream by code
        response = {"error": {"message": "Provider down", "code": "provider_error"}}
        error = parse_error(response)
        assert isinstance(error, UpstreamError)
