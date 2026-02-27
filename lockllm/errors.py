"""Exception hierarchy for LockLLM SDK."""

from typing import Any, Dict, List, Optional

from .types.scan import ScanResult


class LockLLMError(Exception):
    """Base exception for all LockLLM errors.

    Attributes:
        message: Human-readable error description
        type: Error type identifier
        code: Specific error code
        status: HTTP status code
        request_id: Request ID for tracking
    """

    def __init__(
        self,
        message: str,
        error_type: str = "lockllm_error",
        code: Optional[str] = None,
        status: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.type = error_type
        self.code = code
        self.status = status
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"(code: {self.code})")
        if self.request_id:
            parts.append(f"[request_id: {self.request_id}]")
        return " ".join(parts)


class AuthenticationError(LockLLMError):
    """Raised when authentication fails (401).

    This error indicates that the provided API key is invalid or missing.
    Get your API key from
    https://www.lockllm.com/dashboard
    """

    def __init__(self, message: str, request_id: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            error_type="authentication_error",
            code="unauthorized",
            status=401,
            request_id=request_id,
        )


class RateLimitError(LockLLMError):
    """Raised when rate limit is exceeded (429).

    Attributes:
        retry_after: Milliseconds to wait before retrying (optional)
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="rate_limit_error",
            code="rate_limited",
            status=429,
            request_id=request_id,
        )
        self.retry_after = retry_after


class PromptInjectionError(LockLLMError):
    """Raised when malicious prompt is detected (400).

    This error indicates that the input contains a potential security threat
    such as prompt injection, jailbreak attempt, or other adversarial attack.

    Attributes:
        scan_result: Detailed scan results with threat scores
    """

    def __init__(
        self,
        message: str,
        scan_result: ScanResult,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="lockllm_security_error",
            code="prompt_injection_detected",
            status=400,
            request_id=request_id,
        )
        self.scan_result = scan_result


class PolicyViolationError(LockLLMError):
    """Raised when custom policy violation is detected (403).

    This error indicates that the input violates one or more
    custom content policies defined by the user.

    Attributes:
        violated_policies: List of violated policy details
    """

    def __init__(
        self,
        message: str,
        violated_policies: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="lockllm_policy_error",
            code="policy_violation",
            status=403,
            request_id=request_id,
        )
        self.violated_policies = violated_policies or []


class AbuseDetectedError(LockLLMError):
    """Raised when abuse is detected (400).

    This error indicates that the request exhibits patterns
    consistent with automated misuse or abuse.

    Attributes:
        abuse_details: Detailed abuse detection results
    """

    def __init__(
        self,
        message: str,
        abuse_details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="lockllm_abuse_error",
            code="abuse_detected",
            status=400,
            request_id=request_id,
        )
        self.abuse_details = abuse_details or {}


class PIIDetectedError(LockLLMError):
    """Raised when PII is detected and action is block (403).

    This error indicates that personally identifiable information
    was found in the input and the PII action was set to "block".

    Attributes:
        entity_types: List of PII entity types detected
        entity_count: Number of PII entities found
    """

    def __init__(
        self,
        message: str,
        entity_types: Optional[List[str]] = None,
        entity_count: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="lockllm_pii_error",
            code="pii_detected",
            status=403,
            request_id=request_id,
        )
        self.entity_types = entity_types or []
        self.entity_count = entity_count or 0


class InsufficientCreditsError(LockLLMError):
    """Raised when user has insufficient credits (402).

    This error indicates that the user's credit balance is too low
    to process the request. Top up credits at
    https://www.lockllm.com/dashboard/billing

    Attributes:
        current_balance: Current credit balance
        estimated_cost: Estimated cost of the request
    """

    def __init__(
        self,
        message: str,
        current_balance: Optional[float] = None,
        estimated_cost: Optional[float] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="lockllm_balance_error",
            code="insufficient_credits",
            status=402,
            request_id=request_id,
        )
        self.current_balance = current_balance
        self.estimated_cost = estimated_cost


class UpstreamError(LockLLMError):
    """Raised when upstream provider fails (502).

    Attributes:
        provider: Provider name (optional)
        upstream_status: Provider's HTTP status code (optional)
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        upstream_status: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="upstream_error",
            code="provider_error",
            status=502,
            request_id=request_id,
        )
        self.provider = provider
        self.upstream_status = upstream_status


class ConfigurationError(LockLLMError):
    """Raised when configuration is invalid (400).

    This error indicates that the SDK configuration or request parameters
    are invalid or missing required values.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_type="configuration_error",
            code="invalid_config",
            status=400,
        )


class NetworkError(LockLLMError):
    """Raised when network request fails.

    This error indicates a network connectivity issue such as timeout,
    connection refused, or DNS resolution failure.

    Attributes:
        cause: The underlying exception that caused this error (optional)
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="network_error",
            code="connection_failed",
            status=0,
            request_id=request_id,
        )
        self.cause = cause


def parse_error(
    response: Dict[str, Any], request_id: Optional[str] = None
) -> LockLLMError:
    """Parse API error response and return appropriate exception.

    Args:
        response: The error response body from the API
        request_id: Request ID for tracking

    Returns:
        Appropriate LockLLMError subclass based on error type
    """
    error = response.get("error", {})

    if not error:
        return LockLLMError(
            message="Unknown error occurred",
            error_type="unknown_error",
            request_id=request_id,
        )

    # Handle flat error format: {"error": "string_code", "message": "..."}
    if isinstance(error, str):
        message = response.get("message", error)
        error_type = error
        code = error
        request_id = response.get("request_id", request_id)
        return LockLLMError(
            message=message,
            error_type=error_type,
            code=code,
            request_id=request_id,
        )

    message = error.get("message", "An error occurred")
    error_type = error.get("type", "unknown_error")
    code = error.get("code")

    # Prompt injection error
    if code == "prompt_injection_detected" and "scan_result" in error:
        scan_data = error["scan_result"]
        # Filter to known ScanResult fields to avoid TypeError on new fields
        known_fields = {"safe", "label", "confidence", "injection", "sensitivity"}
        filtered_data = {k: v for k, v in scan_data.items() if k in known_fields}
        return PromptInjectionError(
            message=message,
            scan_result=ScanResult(**filtered_data),
            request_id=error.get("request_id", request_id),
        )

    # Policy violation error
    if code == "policy_violation":
        return PolicyViolationError(
            message=message,
            violated_policies=error.get("violated_policies"),
            request_id=error.get("request_id", request_id),
        )

    # Abuse detected error
    if code == "abuse_detected":
        return AbuseDetectedError(
            message=message,
            abuse_details=error.get("abuse_details"),
            request_id=error.get("request_id", request_id),
        )

    # PII detected error
    if code == "pii_detected":
        pii_details = error.get("pii_details", {})
        return PIIDetectedError(
            message=message,
            entity_types=pii_details.get("entity_types", []),
            entity_count=pii_details.get("entity_count", 0),
            request_id=error.get("request_id", request_id),
        )

    # Insufficient credits error
    insufficient_codes = (
        "insufficient_credits",
        "no_balance",
        "insufficient_routing_credits",
        "balance_check_failed",
        "credits_unavailable",
    )
    if code in insufficient_codes or error_type == "lockllm_balance_error":
        return InsufficientCreditsError(
            message=message,
            current_balance=error.get("current_balance"),
            estimated_cost=error.get("estimated_cost"),
            request_id=error.get("request_id", request_id),
        )

    # Authentication error
    if error_type == "authentication_error" or code == "unauthorized":
        return AuthenticationError(message, request_id)

    # Rate limit error
    if error_type == "rate_limit_error" or code == "rate_limited":
        return RateLimitError(message, request_id=request_id)

    # Upstream error
    if error_type == "upstream_error" or code == "provider_error":
        return UpstreamError(message, request_id=request_id)

    # Configuration error
    config_types = ("configuration_error", "lockllm_config_error")
    config_codes = (
        "no_upstream_key",
        "no_byok_key",
        "invalid_provider_for_credits_mode",
    )
    if error_type in config_types or code in config_codes:
        return ConfigurationError(message)

    # Generic error
    return LockLLMError(
        message=message,
        error_type=error_type,
        code=code,
        request_id=request_id,
    )
