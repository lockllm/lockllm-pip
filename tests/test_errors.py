"""Tests for error handling."""

import pytest

from lockllm.errors import (
    AbuseDetectedError,
    AuthenticationError,
    ConfigurationError,
    InsufficientCreditsError,
    LockLLMError,
    NetworkError,
    PolicyViolationError,
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


class TestPolicyViolationError:
    """Tests for PolicyViolationError."""

    def test_policy_violation_error_basic(self):
        """Test basic policy violation error creation."""
        error = PolicyViolationError(
            "Policy violated", request_id="req_123"
        )

        assert error.message == "Policy violated"
        assert error.type == "lockllm_policy_error"
        assert error.code == "policy_violation"
        assert error.status == 403
        assert error.violated_policies == []
        assert error.request_id == "req_123"

    def test_policy_violation_error_with_policies(self):
        """Test policy violation error with violated policies list."""
        policies = [
            {"policy_name": "No violence", "violated_categories": [{"name": "Violence"}]},
            {"policy_name": "No hate", "violated_categories": [{"name": "Hate speech"}]},
        ]
        error = PolicyViolationError(
            "Policy violated",
            violated_policies=policies,
            request_id="req_456",
        )

        assert len(error.violated_policies) == 2
        assert error.violated_policies[0]["policy_name"] == "No violence"


class TestAbuseDetectedError:
    """Tests for AbuseDetectedError."""

    def test_abuse_detected_error_basic(self):
        """Test basic abuse detected error creation."""
        error = AbuseDetectedError(
            "Abuse detected", request_id="req_123"
        )

        assert error.message == "Abuse detected"
        assert error.type == "lockllm_abuse_error"
        assert error.code == "abuse_detected"
        assert error.status == 400
        assert error.abuse_details == {}
        assert error.request_id == "req_123"

    def test_abuse_detected_error_with_details(self):
        """Test abuse detected error with details."""
        details = {
            "confidence": 95,
            "abuse_types": ["bot_generated", "rapid_requests"],
        }
        error = AbuseDetectedError(
            "Abuse detected",
            abuse_details=details,
            request_id="req_456",
        )

        assert error.abuse_details == details
        assert error.abuse_details["confidence"] == 95


class TestPIIDetectedError:
    """Tests for PIIDetectedError."""

    def test_pii_detected_error_basic(self):
        """Test basic PII detected error creation."""
        from lockllm.errors import PIIDetectedError

        error = PIIDetectedError(
            "PII detected in input", request_id="req_123"
        )

        assert error.message == "PII detected in input"
        assert error.type == "lockllm_pii_error"
        assert error.code == "pii_detected"
        assert error.status == 403
        assert error.entity_types == []
        assert error.entity_count == 0
        assert error.request_id == "req_123"

    def test_pii_detected_error_with_details(self):
        """Test PII detected error with entity details."""
        from lockllm.errors import PIIDetectedError

        error = PIIDetectedError(
            "PII detected",
            entity_types=["email", "phone", "ssn"],
            entity_count=5,
            request_id="req_456",
        )

        assert error.entity_types == ["email", "phone", "ssn"]
        assert error.entity_count == 5


class TestInsufficientCreditsError:
    """Tests for InsufficientCreditsError."""

    def test_insufficient_credits_error_basic(self):
        """Test basic insufficient credits error creation."""
        error = InsufficientCreditsError(
            "Not enough credits", request_id="req_123"
        )

        assert error.message == "Not enough credits"
        assert error.type == "lockllm_balance_error"
        assert error.code == "insufficient_credits"
        assert error.status == 402
        assert error.current_balance is None
        assert error.estimated_cost is None
        assert error.request_id == "req_123"

    def test_insufficient_credits_error_with_amounts(self):
        """Test insufficient credits error with balance details."""
        error = InsufficientCreditsError(
            "Not enough credits",
            current_balance=0.50,
            estimated_cost=1.00,
            request_id="req_456",
        )

        assert error.current_balance == 0.50
        assert error.estimated_cost == 1.00


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

    def test_parse_policy_violation_error(self):
        """Test parsing policy violation error."""
        response = {
            "error": {
                "message": "Content violates policy",
                "type": "lockllm_policy_error",
                "code": "policy_violation",
                "request_id": "req_policy",
                "violated_policies": [
                    {"policy_name": "No violence", "violated_categories": []},
                ],
            }
        }

        error = parse_error(response)

        assert isinstance(error, PolicyViolationError)
        assert error.message == "Content violates policy"
        assert error.request_id == "req_policy"
        assert len(error.violated_policies) == 1

    def test_parse_abuse_detected_error(self):
        """Test parsing abuse detected error."""
        response = {
            "error": {
                "message": "Abuse detected in request",
                "type": "lockllm_abuse_error",
                "code": "abuse_detected",
                "request_id": "req_abuse",
                "abuse_details": {
                    "confidence": 95,
                    "abuse_types": ["bot_generated"],
                },
            }
        }

        error = parse_error(response)

        assert isinstance(error, AbuseDetectedError)
        assert error.message == "Abuse detected in request"
        assert error.request_id == "req_abuse"
        assert error.abuse_details["confidence"] == 95

    def test_parse_insufficient_credits_error(self):
        """Test parsing insufficient credits error."""
        response = {
            "error": {
                "message": "Insufficient credits",
                "type": "lockllm_balance_error",
                "code": "insufficient_credits",
                "request_id": "req_credits",
                "current_balance": 0.5,
                "estimated_cost": 1.0,
            }
        }

        error = parse_error(response)

        assert isinstance(error, InsufficientCreditsError)
        assert error.message == "Insufficient credits"
        assert error.request_id == "req_credits"
        assert error.current_balance == 0.5
        assert error.estimated_cost == 1.0

    def test_parse_insufficient_credits_by_code_no_balance(self):
        """Test parsing insufficient credits by no_balance code."""
        response = {
            "error": {
                "message": "No balance available",
                "type": "some_type",
                "code": "no_balance",
            }
        }

        error = parse_error(response)
        assert isinstance(error, InsufficientCreditsError)

    def test_parse_insufficient_credits_by_code_routing(self):
        """Test parsing insufficient routing credits error."""
        response = {
            "error": {
                "message": "Not enough for routing",
                "type": "some_type",
                "code": "insufficient_routing_credits",
            }
        }

        error = parse_error(response)
        assert isinstance(error, InsufficientCreditsError)

    def test_parse_insufficient_credits_by_code_balance_check(self):
        """Test parsing balance check failed error."""
        response = {
            "error": {
                "message": "Balance check failed",
                "type": "some_type",
                "code": "balance_check_failed",
            }
        }

        error = parse_error(response)
        assert isinstance(error, InsufficientCreditsError)

    def test_parse_insufficient_credits_by_type(self):
        """Test parsing insufficient credits by error type."""
        response = {
            "error": {
                "message": "Balance too low",
                "type": "lockllm_balance_error",
                "code": "some_code",
            }
        }

        error = parse_error(response)
        assert isinstance(error, InsufficientCreditsError)

    def test_parse_configuration_error_no_byok_key(self):
        """Test parsing configuration error with no_byok_key code."""
        response = {
            "error": {
                "message": "No BYOK key configured",
                "type": "some_type",
                "code": "no_byok_key",
            }
        }

        error = parse_error(response)
        assert isinstance(error, ConfigurationError)

    def test_parse_configuration_error_invalid_provider(self):
        """Test parsing configuration error with invalid_provider_for_credits_mode code."""
        response = {
            "error": {
                "message": "Invalid provider for credits mode",
                "type": "some_type",
                "code": "invalid_provider_for_credits_mode",
            }
        }

        error = parse_error(response)
        assert isinstance(error, ConfigurationError)

    def test_parse_configuration_error_by_type(self):
        """Test parsing configuration error by lockllm_config_error type."""
        response = {
            "error": {
                "message": "Config issue",
                "type": "lockllm_config_error",
            }
        }

        error = parse_error(response)
        assert isinstance(error, ConfigurationError)

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

    def test_parse_prompt_injection_with_extra_scan_fields(self):
        """Test that unknown fields in scan_result are filtered out."""
        response = {
            "error": {
                "message": "Injection found",
                "type": "lockllm_security_error",
                "code": "prompt_injection_detected",
                "scan_result": {
                    "safe": False,
                    "label": 1,
                    "confidence": 90.0,
                    "injection": 85.0,
                    "sensitivity": "medium",
                    "unknown_new_field": "should_be_filtered",
                },
            }
        }

        error = parse_error(response)

        assert isinstance(error, PromptInjectionError)
        assert error.scan_result.safe is False
        assert error.scan_result.confidence == 90.0

    def test_parse_error_default_message(self):
        """Test parsing error with missing message."""
        response = {
            "error": {
                "type": "unknown_type",
            }
        }

        error = parse_error(response)
        assert error.message == "An error occurred"

    def test_parse_flat_error_string_format(self):
        """Test parsing flat error format where error is a string code."""
        response = {
            "error": "bad_request",
            "message": "Invalid input provided",
            "request_id": "req_flat",
        }

        error = parse_error(response, request_id="req_fallback")

        assert isinstance(error, LockLLMError)
        assert error.message == "Invalid input provided"
        assert error.type == "bad_request"
        assert error.code == "bad_request"
        assert error.request_id == "req_flat"

    def test_parse_flat_error_string_without_message(self):
        """Test parsing flat error format without explicit message."""
        response = {
            "error": "some_error_code",
        }

        error = parse_error(response)

        assert isinstance(error, LockLLMError)
        assert error.message == "some_error_code"
        assert error.type == "some_error_code"
        assert error.code == "some_error_code"

    def test_parse_pii_detected_error(self):
        """Test parsing PII detected error."""
        from lockllm.errors import PIIDetectedError

        response = {
            "error": {
                "message": "PII detected in input",
                "type": "lockllm_pii_error",
                "code": "pii_detected",
                "request_id": "req_pii",
                "pii_details": {
                    "entity_types": ["email", "phone"],
                    "entity_count": 3,
                },
            }
        }

        error = parse_error(response)

        assert isinstance(error, PIIDetectedError)
        assert error.message == "PII detected in input"
        assert error.request_id == "req_pii"
        assert error.entity_types == ["email", "phone"]
        assert error.entity_count == 3

    def test_parse_pii_detected_error_empty_details(self):
        """Test parsing PII detected error with empty pii_details."""
        from lockllm.errors import PIIDetectedError

        response = {
            "error": {
                "message": "PII found",
                "type": "lockllm_pii_error",
                "code": "pii_detected",
            }
        }

        error = parse_error(response)

        assert isinstance(error, PIIDetectedError)
        assert error.entity_types == []
        assert error.entity_count == 0
