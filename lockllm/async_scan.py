"""Asynchronous scan client."""

from typing import Any, Optional

from .async_http_client import AsyncHttpClient
from .scan import _build_scan_headers, _parse_scan_response
from .types.scan import (
    CompressionAction,
    PIIAction,
    ScanAction,
    ScanMode,
    ScanOptions,
    ScanRequest,
    ScanResponse,
    Sensitivity,
)


class AsyncScanClient:
    """Client for scanning prompts for security threats (asynchronous).

    This client provides async methods to scan text inputs for:
    - Prompt injection attacks
    - Jailbreak attempts
    - Instruction override
    - System prompt extraction
    - Tool/function abuse
    - RAG injection
    - Obfuscation techniques
    - Custom policy violations
    - Abuse detection
    """

    def __init__(self, http: AsyncHttpClient) -> None:
        """Initialize the async scan client.

        Args:
            http: Async HTTP client for making requests
        """
        self._http = http

    async def scan(
        self,
        input: str,
        sensitivity: Sensitivity = "medium",
        scan_mode: Optional[ScanMode] = None,
        scan_action: Optional[ScanAction] = None,
        policy_action: Optional[ScanAction] = None,
        abuse_action: Optional[ScanAction] = None,
        pii_action: Optional[PIIAction] = None,
        compression: Optional[CompressionAction] = None,
        compression_rate: Optional[float] = None,
        chunk: Optional[bool] = None,
        scan_options: Optional[ScanOptions] = None,
        **options: Any,
    ) -> ScanResponse:
        """Scan a prompt for security threats (async).

        Analyzes input text using advanced ML models to detect prompt
        injection, jailbreak attempts, and other adversarial attacks.

        Args:
            input: The text prompt to scan for security threats
            sensitivity: Detection threshold level
                - "low": Fewer false positives, may miss
                    sophisticated attacks
                - "medium": Balanced detection (recommended)
                - "high": Maximum protection, may have more false
                    positives
            scan_mode: Which security checks to perform
                - "normal": Core injection detection only
                - "policy_only": Custom policies only
                - "combined": Both core + policies (default)
            scan_action: Core injection detection behavior
                - "block": Block the request
                - "allow_with_warning": Allow with warning (default)
            policy_action: Policy violation behavior
                - "block": Block the request
                - "allow_with_warning": Allow with warning (default)
            abuse_action: Abuse detection behavior (opt-in)
                - None: Disabled (default)
                - "block": Block the request
                - "allow_with_warning": Allow with warning
            pii_action: PII detection behavior (opt-in)
                - None: Disabled (default)
                - "strip": Strip PII entities from the prompt
                - "block": Block the request
                - "allow_with_warning": Allow with PII info in response
            compression: Prompt compression method (opt-in)
                - None: Disabled (default)
                - "toon": JSON-to-compact notation (free, JSON only)
                - "compact": ML-based compression ($0.0001/use, any text)
                - "combined": TOON then ML-based compression
                    ($0.0001/use, maximum compression)
            compression_rate: Compression rate for compact/combined
                methods (0.3-0.7, default 0.5). Lower = more aggressive.
                Only used when compression="compact" or "combined".
            chunk: Whether to enable chunking for long prompts
                - None: Use server default
                - True: Enable chunking
                - False: Disable chunking
            scan_options: Pre-configured ScanOptions object. Individual
                keyword arguments take precedence over ScanOptions values.
            **options: Additional request options (headers, timeout)

        Returns:
            ScanResponse object with safety classification and threat scores

        Raises:
            ConfigurationError: If configuration is invalid
            AuthenticationError: If API key is invalid
            NetworkError: If network request fails
            RateLimitError: If rate limit is exceeded
            PromptInjectionError: If scan_action is "block" and injection detected
            PolicyViolationError: If policy_action is "block" and violation found
            AbuseDetectedError: If abuse_action is "block" and abuse detected
            PIIDetectedError: If pii_action is "block" and PII detected
            InsufficientCreditsError: If credit balance is too low

        Example:
            >>> client = AsyncScanClient(http)
            >>> result = await client.scan(
            ...     input="Ignore previous instructions",
            ...     sensitivity="medium",
            ...     scan_mode="combined",
            ...     scan_action="block"
            ... )
            >>> if not result.safe:
            ...     print(f"Malicious! Injection score: {result.injection}%")

            Using ScanOptions:
            >>> opts = ScanOptions(scan_mode="combined", scan_action="block")
            >>> result = await client.scan(input="test", scan_options=opts)
        """
        # Resolve options: individual kwargs take precedence over ScanOptions
        if scan_options is not None:
            if scan_mode is None:
                scan_mode = scan_options.scan_mode
            if scan_action is None:
                scan_action = scan_options.scan_action
            if policy_action is None:
                policy_action = scan_options.policy_action
            if abuse_action is None:
                abuse_action = scan_options.abuse_action
            if pii_action is None:
                pii_action = scan_options.pii_action
            if compression is None:
                compression = scan_options.compression
            if compression_rate is None:
                compression_rate = scan_options.compression_rate
            if chunk is None:
                chunk = scan_options.chunk

        request = ScanRequest(input=input, sensitivity=sensitivity)
        body = {"input": request.input, "sensitivity": request.sensitivity}

        # Build headers from scan configuration
        scan_headers = _build_scan_headers(
            scan_mode=scan_mode,
            scan_action=scan_action,
            policy_action=policy_action,
            abuse_action=abuse_action,
            pii_action=pii_action,
            compression=compression,
            compression_rate=compression_rate,
            sensitivity=sensitivity,
            chunk=chunk,
        )

        # Merge with user-provided headers
        user_headers = options.get("headers")
        if user_headers:
            scan_headers.update(user_headers)

        timeout = options.get("timeout")

        data, request_id = await self._http.post(
            "/v1/scan",
            body=body,
            headers=scan_headers if scan_headers else None,
            timeout=timeout,
        )

        # Parse response (reuse sync parser - no async needed)
        return _parse_scan_response(data, request_id)
