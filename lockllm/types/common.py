"""Common type definitions."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LockLLMConfig:
    """Configuration for LockLLM client.

    Attributes:
        api_key: Your LockLLM API key from https://www.lockllm.com/dashboard
        base_url: Custom base URL (default: https://api.lockllm.com)
        timeout: Request timeout in seconds (default: 60.0)
        max_retries: Maximum number of retry attempts (default: 3)
    """

    api_key: str
    base_url: str = "https://api.lockllm.com"
    timeout: float = 60.0
    max_retries: int = 3


@dataclass
class RequestOptions:
    """Optional request configuration.

    Attributes:
        headers: Additional HTTP headers to include
        timeout: Override default timeout for this request
    """

    headers: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None


@dataclass
class ProxyOptions:
    """Configuration options for proxy requests via wrapper functions.

    Controls how LockLLM scans and routes requests sent through
    provider wrappers (create_openai, create_anthropic, etc.).

    These options are converted to X-LockLLM-* HTTP headers
    that are sent with every request through the proxy.

    Attributes:
        scan_mode: Which security checks to perform
            - "normal": Core injection detection only
            - "policy_only": Custom policies only
            - "combined": Both core + policies (default)
        scan_action: Behavior when core injection is detected
            - "block": Block the request
            - "allow_with_warning": Allow with warning (default)
        policy_action: Behavior when custom policy violation is found
            - "block": Block the request
            - "allow_with_warning": Allow with warning (default)
        abuse_action: Behavior when abuse is detected (opt-in)
            - None: Abuse detection disabled (default)
            - "block": Block the request
            - "allow_with_warning": Allow with warning
        route_action: Intelligent routing mode
            - "disabled": No routing, use original model (default)
            - "auto": AI-powered automatic routing
            - "custom": Use user-defined routing rules
        sensitivity: Scan sensitivity threshold level
            - None: Use server default ("medium")
            - "low": Fewer false positives, may miss sophisticated attacks
            - "medium": Balanced detection (recommended)
            - "high": Maximum protection, may have more false positives
        cache_response: Whether to cache LLM responses
            - None: Use server default (enabled)
            - True: Enable response caching
            - False: Disable response caching
        cache_ttl: Cache TTL in seconds (max 86400/24 hours)
            - None: Use server default (3600/1 hour)
        chunk: Whether to enable chunking for long prompts
            - None: Use server default
            - True: Enable chunking
            - False: Disable chunking
        pii_action: PII detection behavior (opt-in)
            - None: PII detection disabled (default)
            - "strip": Strip PII entities from the prompt
            - "block": Block the request
            - "allow_with_warning": Allow with PII info in response
    """

    scan_mode: Optional[str] = None
    scan_action: Optional[str] = None
    policy_action: Optional[str] = None
    abuse_action: Optional[str] = None
    route_action: Optional[str] = None
    sensitivity: Optional[str] = None
    cache_response: Optional[bool] = None
    cache_ttl: Optional[int] = None
    chunk: Optional[bool] = None
    pii_action: Optional[str] = None


@dataclass
class ProxyScanWarning:
    """Scan warning metadata from proxy response headers.

    Attributes:
        injection_score: Injection score from scan (0-100)
        confidence: Confidence level of the detection (0-100)
        detail: Base64-encoded JSON with detailed scan info
    """

    injection_score: float
    confidence: float
    detail: str


@dataclass
class ProxyPolicyWarnings:
    """Policy warning metadata from proxy response headers.

    Attributes:
        count: Number of policy violations detected
        confidence: Confidence level of the detection (0-100)
        detail: Base64-encoded JSON with violation details
    """

    count: int
    confidence: float
    detail: str


@dataclass
class ProxyAbuseDetected:
    """Abuse detection metadata from proxy response headers.

    Attributes:
        confidence: Confidence level of abuse detection (0-100)
        types: Comma-separated abuse types detected
        detail: Base64-encoded JSON with abuse details
    """

    confidence: float
    types: str
    detail: str


@dataclass
class ProxyPIIDetected:
    """PII detection metadata from proxy response headers.

    Attributes:
        detected: Whether PII was detected
        entity_types: Comma-separated PII entity types detected
        entity_count: Number of PII entities found
        action: PII action taken (strip, block, allow_with_warning)
    """

    detected: bool
    entity_types: str
    entity_count: int
    action: str


@dataclass
class ProxyRoutingMetadata:
    """Routing metadata from proxy response headers.

    Attributes:
        enabled: Whether routing was applied
        task_type: Detected task classification
        complexity: Prompt complexity score (0-1)
        selected_model: Model chosen by router
        routing_reason: Explanation for model selection
        original_provider: Original provider requested
        original_model: Original model requested
        estimated_savings: Estimated cost savings
        estimated_original_cost: Estimated cost with original model
        estimated_routed_cost: Estimated cost with routed model
        estimated_input_tokens: Estimated input tokens for routing
        estimated_output_tokens: Estimated output tokens for routing
        routing_fee_reason: Reason for routing fee or waiver
    """

    enabled: bool
    task_type: str
    complexity: float
    selected_model: str
    routing_reason: str
    original_provider: str
    original_model: str
    estimated_savings: float
    estimated_original_cost: Optional[float] = None
    estimated_routed_cost: Optional[float] = None
    estimated_input_tokens: Optional[int] = None
    estimated_output_tokens: Optional[int] = None
    routing_fee_reason: Optional[str] = None


@dataclass
class ProxyResponseMetadata:
    """Parsed metadata from proxy response headers.

    Contains scan results, policy warnings, abuse detection,
    routing info, and credit tracking from X-LockLLM-* headers.

    Attributes:
        request_id: Unique request identifier
        scanned: Whether the request was scanned
        safe: Whether the request was classified as safe
        scan_mode: Scan mode used (normal, policy_only, combined)
        credits_mode: Credit mode (lockllm_credits or byok)
        provider: AI provider name
        model: Model identifier (if available)
        sensitivity: Detection sensitivity level used
        label: Binary classification (0=safe, 1=unsafe)
        policy_confidence: Policy check confidence (0-100)
        scan_warning: Scan warning details (if detected)
        policy_warnings: Policy violation details (if detected)
        abuse_detected: Abuse detection details (if detected)
        pii_detected: PII detection details (if PII detection enabled)
        routing: Routing metadata (if routing was enabled)
        credits_reserved: Credits reserved for request
        routing_fee_reserved: Routing fee reserved
        routing_fee_reason: Reason when no routing fee charged
        credits_deducted: Credits actually deducted (async, may be None)
        balance_after: Balance after deduction (async, may be None)
        blocked: Whether the request was blocked
        estimated_original_cost: Estimated cost with original model
        estimated_routed_cost: Estimated cost with routed model
        estimated_input_tokens: Estimated input tokens for routing
        estimated_output_tokens: Estimated output tokens for routing
        cache_status: Response cache status ("HIT" or "MISS")
        cache_age: Age of cached response in seconds
        tokens_saved: Number of tokens saved by cache hit
        cost_saved: Cost saved by cache hit
        scan_detail: Decoded scan detail from base64 header
        policy_detail: Decoded policy warning detail from base64 header
        abuse_detail: Decoded abuse detail from base64 header
    """

    request_id: str
    scanned: bool
    safe: bool
    scan_mode: str
    credits_mode: str
    provider: str
    model: Optional[str] = None
    sensitivity: Optional[str] = None
    label: Optional[int] = None
    policy_confidence: Optional[float] = None
    scan_warning: Optional[ProxyScanWarning] = None
    policy_warnings: Optional[ProxyPolicyWarnings] = None
    abuse_detected: Optional[ProxyAbuseDetected] = None
    pii_detected: Optional[ProxyPIIDetected] = None
    routing: Optional[ProxyRoutingMetadata] = None
    credits_reserved: Optional[float] = None
    routing_fee_reserved: Optional[float] = None
    routing_fee_reason: Optional[str] = None
    credits_deducted: Optional[float] = None
    balance_after: Optional[float] = None
    blocked: Optional[bool] = None
    estimated_original_cost: Optional[float] = None
    estimated_routed_cost: Optional[float] = None
    estimated_input_tokens: Optional[int] = None
    estimated_output_tokens: Optional[int] = None
    cache_status: Optional[str] = None
    cache_age: Optional[int] = None
    tokens_saved: Optional[int] = None
    cost_saved: Optional[float] = None
    scan_detail: Optional[Any] = None
    policy_detail: Optional[Any] = None
    abuse_detail: Optional[Any] = None
