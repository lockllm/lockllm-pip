"""Utility functions for LockLLM SDK."""

import base64
import hashlib
import json
import random
import string
import time
from typing import Any, Dict, Optional, cast

from .types.common import (
    ProxyAbuseDetected,
    ProxyOptions,
    ProxyPolicyWarnings,
    ProxyResponseMetadata,
    ProxyRoutingMetadata,
    ProxyScanWarning,
)
from .types.providers import PROVIDER_BASE_URLS, UNIVERSAL_PROXY_URL, ProviderName


def generate_request_id() -> str:
    """Generate a unique request ID.

    Returns:
        A random 16-character hexadecimal string
    """
    random_bytes = "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return hashlib.md5(f"{time.time()}{random_bytes}".encode()).hexdigest()[:16]


def calculate_backoff(
    attempt: int, base_delay: int = 1000, max_delay: int = 30000
) -> int:
    """Calculate exponential backoff delay in milliseconds.

    Args:
        attempt: The retry attempt number (0-indexed)
        base_delay: Base delay in milliseconds (default: 1000)
        max_delay: Maximum delay in milliseconds (default: 30000)

    Returns:
        Delay in milliseconds with exponential backoff
    """
    delay = min(base_delay * (2**attempt), max_delay)
    # Add jitter to avoid thundering herd
    jitter = random.uniform(0, 0.1 * delay)
    return int(delay + jitter)


def parse_retry_after(retry_after: Optional[str]) -> Optional[int]:
    """Parse Retry-After header to milliseconds.

    Args:
        retry_after: Value from Retry-After header (seconds or HTTP date)

    Returns:
        Delay in milliseconds, or None if parsing fails
    """
    if not retry_after:
        return None

    try:
        # Try as seconds
        return int(retry_after) * 1000
    except ValueError:
        # Try as HTTP date
        try:
            from datetime import datetime, timezone
            from email.utils import parsedate_to_datetime

            date = parsedate_to_datetime(retry_after)
            now = datetime.now(timezone.utc)
            delta = (date - now).total_seconds()
            return max(0, int(delta * 1000))
        except Exception:
            return None


def get_proxy_url(provider: ProviderName) -> str:
    """Get the proxy URL for a specific provider.

    Args:
        provider: Name of the provider

    Returns:
        Full proxy URL for the provider

    Example:
        >>> get_proxy_url('openai')
        'https://api.lockllm.com/v1/proxy/openai'
    """
    return PROVIDER_BASE_URLS[provider]


def get_all_proxy_urls() -> Dict[ProviderName, str]:
    """Get proxy URLs for all supported providers.

    Returns:
        Dictionary mapping provider names to proxy URLs

    Example:
        >>> urls = get_all_proxy_urls()
        >>> urls['openai']
        'https://api.lockllm.com/v1/proxy/openai'
    """
    return cast(Dict[ProviderName, str], PROVIDER_BASE_URLS.copy())


def get_universal_proxy_url() -> str:
    """Get the universal proxy URL for non-BYOK users.

    This endpoint uses LockLLM credits and supports 200+ models.
    No BYOK API key configuration required.

    Returns:
        Universal proxy URL

    Example:
        >>> get_universal_proxy_url()
        'https://api.lockllm.com/v1/proxy'
    """
    return UNIVERSAL_PROXY_URL


def build_lockllm_headers(options: ProxyOptions) -> Dict[str, str]:
    """Convert ProxyOptions to X-LockLLM-* HTTP headers.

    Builds a dictionary of HTTP headers from the provided proxy
    configuration options. Only includes headers for options that
    are explicitly set (not None).

    Args:
        options: Proxy configuration options

    Returns:
        Dictionary of X-LockLLM-* HTTP headers

    Example:
        >>> from lockllm import ProxyOptions, build_lockllm_headers
        >>> opts = ProxyOptions(
        ...     scan_action="block",
        ...     route_action="auto"
        ... )
        >>> headers = build_lockllm_headers(opts)
        >>> headers
        {'X-LockLLM-Scan-Action': 'block', 'X-LockLLM-Route-Action': 'auto'}
    """
    headers: Dict[str, str] = {}

    if options.scan_mode is not None:
        headers["X-LockLLM-Scan-Mode"] = options.scan_mode
    if options.scan_action is not None:
        headers["X-LockLLM-Scan-Action"] = options.scan_action
    if options.policy_action is not None:
        headers["X-LockLLM-Policy-Action"] = options.policy_action
    if options.abuse_action is not None:
        headers["X-LockLLM-Abuse-Action"] = options.abuse_action
    if options.route_action is not None:
        headers["X-LockLLM-Route-Action"] = options.route_action
    if options.sensitivity is not None:
        headers["X-LockLLM-Sensitivity"] = options.sensitivity
    if options.cache_response is not None:
        headers["X-LockLLM-Cache-Response"] = str(options.cache_response).lower()
    if options.cache_ttl is not None:
        headers["X-LockLLM-Cache-TTL"] = str(options.cache_ttl)
    if options.chunk is not None:
        headers["X-LockLLM-Chunk"] = str(options.chunk).lower()

    return headers


def decode_detail_field(detail: str) -> Optional[Any]:
    """Decode a base64-encoded JSON detail field from response headers.

    Proxy response headers like X-LockLLM-Scan-Detail,
    X-LockLLM-Warning-Detail, and X-LockLLM-Abuse-Detail contain
    base64-encoded JSON strings with detailed information.

    Args:
        detail: Base64-encoded JSON string

    Returns:
        Decoded JSON data, or None if decoding fails

    Example:
        >>> import base64, json
        >>> encoded = base64.b64encode(
        ...     json.dumps({"score": 95}).encode()
        ... ).decode()
        >>> decode_detail_field(encoded)
        {'score': 95}
    """
    try:
        decoded = base64.b64decode(detail).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        return None


def parse_proxy_metadata(headers: Dict[str, str]) -> ProxyResponseMetadata:
    """Parse proxy response headers into a ProxyResponseMetadata object.

    Extracts all X-LockLLM-* response headers from a proxy request
    and returns a typed dataclass with scan results, policy warnings,
    abuse detection, routing info, and credit tracking.

    Args:
        headers: Response headers dictionary

    Returns:
        ProxyResponseMetadata with parsed values

    Example:
        >>> headers = {
        ...     "x-request-id": "abc123",
        ...     "x-lockllm-scanned": "true",
        ...     "x-lockllm-safe": "true",
        ...     "x-lockllm-provider": "openai",
        ... }
        >>> metadata = parse_proxy_metadata(headers)
        >>> metadata.safe
        True
    """
    # Case-insensitive header lookup
    lower_headers = {k.lower(): v for k, v in headers.items()}

    def get_header(name: str) -> Optional[str]:
        return lower_headers.get(name.lower())

    metadata = ProxyResponseMetadata(
        request_id=get_header("x-request-id") or "",
        scanned=get_header("x-lockllm-scanned") == "true",
        safe=get_header("x-lockllm-safe") == "true",
        scan_mode=get_header("x-scan-mode") or "combined",
        credits_mode=get_header("x-lockllm-credits-mode") or "byok",
        provider=get_header("x-lockllm-provider") or "",
        model=get_header("x-lockllm-model"),
    )

    # Parse label
    label = get_header("x-lockllm-label")
    if label is not None:
        try:
            metadata.label = int(label)
        except (ValueError, TypeError):
            pass

    # Parse policy confidence
    policy_confidence = get_header("x-lockllm-policy-confidence")
    if policy_confidence:
        metadata.policy_confidence = float(policy_confidence)

    # Parse blocked flag
    if get_header("x-lockllm-blocked") == "true":
        metadata.blocked = True

    # Parse scan warning
    if get_header("x-lockllm-scan-warning") == "true":
        injection_score = get_header("x-lockllm-injection-score")
        confidence = get_header("x-lockllm-confidence")
        detail = get_header("x-lockllm-scan-detail")
        metadata.scan_warning = ProxyScanWarning(
            injection_score=float(injection_score) if injection_score else 0,
            confidence=float(confidence) if confidence else 0,
            detail=detail or "",
        )

    # Parse policy warnings
    if get_header("x-lockllm-policy-warnings") == "true":
        count = get_header("x-lockllm-warning-count")
        confidence = get_header("x-lockllm-policy-confidence")
        detail = get_header("x-lockllm-warning-detail")
        metadata.policy_warnings = ProxyPolicyWarnings(
            count=int(count) if count else 0,
            confidence=float(confidence) if confidence else 0,
            detail=detail or "",
        )

    # Parse abuse detection
    if get_header("x-lockllm-abuse-detected") == "true":
        confidence = get_header("x-lockllm-abuse-confidence")
        types = get_header("x-lockllm-abuse-types")
        detail = get_header("x-lockllm-abuse-detail")
        metadata.abuse_detected = ProxyAbuseDetected(
            confidence=float(confidence) if confidence else 0,
            types=types or "",
            detail=detail or "",
        )

    # Parse routing metadata
    if get_header("x-lockllm-route-enabled") == "true":
        task_type = get_header("x-lockllm-task-type")
        complexity = get_header("x-lockllm-complexity")
        selected_model = get_header("x-lockllm-selected-model")
        routing_reason = get_header("x-lockllm-routing-reason")
        original_provider = get_header("x-lockllm-original-provider")
        original_model = get_header("x-lockllm-original-model")
        estimated_savings = get_header("x-lockllm-estimated-savings")
        metadata.routing = ProxyRoutingMetadata(
            enabled=True,
            task_type=task_type or "",
            complexity=float(complexity) if complexity else 0,
            selected_model=selected_model or "",
            routing_reason=routing_reason or "",
            original_provider=original_provider or "",
            original_model=original_model or "",
            estimated_savings=float(estimated_savings) if estimated_savings else 0,
        )

    # Parse credit tracking
    credits_reserved = get_header("x-lockllm-credits-reserved")
    if credits_reserved:
        metadata.credits_reserved = float(credits_reserved)

    routing_fee_reserved = get_header("x-lockllm-routing-fee-reserved")
    if routing_fee_reserved:
        metadata.routing_fee_reserved = float(routing_fee_reserved)

    routing_fee_reason = get_header("x-lockllm-routing-fee-reason")
    if routing_fee_reason:
        metadata.routing_fee_reason = routing_fee_reason

    credits_deducted = get_header("x-lockllm-credits-deducted")
    if credits_deducted:
        metadata.credits_deducted = float(credits_deducted)

    balance_after = get_header("x-lockllm-balance-after")
    if balance_after:
        metadata.balance_after = float(balance_after)

    # Parse routing cost estimates
    estimated_original_cost = get_header("x-lockllm-estimated-original-cost")
    if estimated_original_cost:
        metadata.estimated_original_cost = float(estimated_original_cost)

    estimated_routed_cost = get_header("x-lockllm-estimated-routed-cost")
    if estimated_routed_cost:
        metadata.estimated_routed_cost = float(estimated_routed_cost)

    estimated_input_tokens = get_header("x-lockllm-estimated-input-tokens")
    if estimated_input_tokens:
        metadata.estimated_input_tokens = int(estimated_input_tokens)

    estimated_output_tokens = get_header("x-lockllm-estimated-output-tokens")
    if estimated_output_tokens:
        metadata.estimated_output_tokens = int(estimated_output_tokens)

    # Parse response cache metadata
    cache_status = get_header("x-lockllm-cache-status")
    if cache_status:
        metadata.cache_status = cache_status

    cache_age = get_header("x-lockllm-cache-age")
    if cache_age:
        metadata.cache_age = int(cache_age)

    tokens_saved = get_header("x-lockllm-tokens-saved")
    if tokens_saved:
        metadata.tokens_saved = int(tokens_saved)

    cost_saved = get_header("x-lockllm-cost-saved")
    if cost_saved:
        metadata.cost_saved = float(cost_saved)

    return metadata
