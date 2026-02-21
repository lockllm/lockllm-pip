"""Synchronous scan client."""

from typing import Any, Dict, List, Optional

from .http_client import HttpClient
from .types.scan import (
    AbuseWarning,
    Debug,
    PIIAction,
    PIIResult,
    PolicyViolation,
    RoutingInfo,
    ScanAction,
    ScanMode,
    ScanOptions,
    ScanRequest,
    ScanResponse,
    ScanWarning,
    Sensitivity,
    Usage,
    ViolatedCategory,
)


class ScanClient:
    """Client for scanning prompts for security threats (synchronous).

    This client provides methods to scan text inputs for:
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

    def __init__(self, http: HttpClient) -> None:
        """Initialize the scan client.

        Args:
            http: HTTP client for making requests
        """
        self._http = http

    def scan(
        self,
        input: str,
        sensitivity: Sensitivity = "medium",
        scan_mode: Optional[ScanMode] = None,
        scan_action: Optional[ScanAction] = None,
        policy_action: Optional[ScanAction] = None,
        abuse_action: Optional[ScanAction] = None,
        pii_action: Optional[PIIAction] = None,
        chunk: Optional[bool] = None,
        scan_options: Optional[ScanOptions] = None,
        **options: Any,
    ) -> ScanResponse:
        """Scan a prompt for security threats.

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
            >>> client = ScanClient(http)
            >>> result = client.scan(
            ...     input="Ignore previous instructions",
            ...     sensitivity="medium",
            ...     scan_mode="combined",
            ...     scan_action="block"
            ... )
            >>> if not result.safe:
            ...     print(f"Malicious! Injection score: {result.injection}%")

            Using ScanOptions:
            >>> opts = ScanOptions(scan_mode="combined", scan_action="block")
            >>> result = client.scan(input="test", scan_options=opts)
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
            sensitivity=sensitivity,
            chunk=chunk,
        )

        # Merge with user-provided headers
        user_headers = options.get("headers")
        if user_headers:
            scan_headers.update(user_headers)

        timeout = options.get("timeout")

        data, request_id = self._http.post(
            "/v1/scan",
            body=body,
            headers=scan_headers if scan_headers else None,
            timeout=timeout,
        )

        # Parse response
        return _parse_scan_response(data, request_id)


def _build_scan_headers(
    scan_mode: Optional[ScanMode] = None,
    scan_action: Optional[ScanAction] = None,
    policy_action: Optional[ScanAction] = None,
    abuse_action: Optional[ScanAction] = None,
    pii_action: Optional[PIIAction] = None,
    sensitivity: Optional[Sensitivity] = None,
    chunk: Optional[bool] = None,
) -> Dict[str, str]:
    """Build X-LockLLM-* headers from scan configuration options."""
    headers: Dict[str, str] = {}
    if scan_mode is not None:
        headers["X-LockLLM-Scan-Mode"] = scan_mode
    if scan_action is not None:
        headers["X-LockLLM-Scan-Action"] = scan_action
    if policy_action is not None:
        headers["X-LockLLM-Policy-Action"] = policy_action
    if abuse_action is not None:
        headers["X-LockLLM-Abuse-Action"] = abuse_action
    if pii_action is not None:
        headers["X-LockLLM-PII-Action"] = pii_action
    if sensitivity is not None:
        headers["X-LockLLM-Sensitivity"] = sensitivity
    if chunk is not None:
        headers["X-LockLLM-Chunk"] = str(chunk).lower()
    return headers


def _parse_scan_response(data: dict, request_id: str) -> ScanResponse:
    """Parse API response into ScanResponse.

    Args:
        data: Response data from API
        request_id: Request ID

    Returns:
        Parsed ScanResponse object
    """
    # Parse usage
    usage_data = data.get("usage", {})
    usage = Usage(
        requests=usage_data.get("requests", 0),
        input_chars=usage_data.get("input_chars", 0),
    )

    # Parse debug (optional, Pro plan only)
    debug: Optional[Debug] = None
    if "debug" in data:
        debug_data = data["debug"]
        debug = Debug(
            duration_ms=debug_data.get("duration_ms", 0),
            inference_ms=debug_data.get("inference_ms", 0),
            mode=debug_data.get("mode", "single"),
        )

    # Parse policy warnings (optional)
    policy_warnings: Optional[List[PolicyViolation]] = None
    if "policy_warnings" in data and data["policy_warnings"]:
        policy_warnings = [
            PolicyViolation(
                policy_name=pw.get("policy_name", ""),
                violated_categories=[
                    ViolatedCategory(
                        name=cat.get("name", ""),
                        description=cat.get("description"),
                    )
                    for cat in pw.get("violated_categories", [])
                ],
                violation_details=pw.get("violation_details"),
            )
            for pw in data["policy_warnings"]
        ]

    # Parse scan warning (optional)
    scan_warning: Optional[ScanWarning] = None
    if "scan_warning" in data and data["scan_warning"]:
        sw = data["scan_warning"]
        scan_warning = ScanWarning(
            message=sw.get("message", ""),
            injection_score=sw.get("injection_score", 0),
            confidence=sw.get("confidence", 0),
            label=sw.get("label", 0),
        )

    # Parse abuse warnings (optional)
    abuse_warnings: Optional[AbuseWarning] = None
    if "abuse_warnings" in data and data["abuse_warnings"]:
        aw = data["abuse_warnings"]
        abuse_warnings = AbuseWarning(
            detected=aw.get("detected", True),
            confidence=aw.get("confidence", 0),
            abuse_types=aw.get("abuse_types", []),
            indicators=aw.get("indicators", {}),
            recommendation=aw.get("recommendation"),
        )

    # Parse routing info (optional)
    routing: Optional[RoutingInfo] = None
    if "routing" in data and data["routing"]:
        rt = data["routing"]
        routing = RoutingInfo(
            enabled=rt.get("enabled", False),
            task_type=rt.get("task_type", "Other"),
            complexity=rt.get("complexity", 0),
            selected_model=rt.get("selected_model"),
            reasoning=rt.get("reasoning"),
            estimated_cost=rt.get("estimated_cost"),
        )

    # Parse PII result (optional)
    pii_result: Optional[PIIResult] = None
    if "pii_result" in data and data["pii_result"]:
        pr = data["pii_result"]
        pii_result = PIIResult(
            detected=pr.get("detected", False),
            entity_types=pr.get("entity_types", []),
            entity_count=pr.get("entity_count", 0),
            redacted_input=pr.get("redacted_input"),
        )

    return ScanResponse(
        safe=data["safe"],
        label=data["label"],
        confidence=data.get("confidence"),
        injection=data.get("injection"),
        sensitivity=data["sensitivity"],
        request_id=data.get("request_id", request_id),
        usage=usage,
        debug=debug,
        policy_confidence=data.get("policy_confidence"),
        policy_warnings=policy_warnings,
        scan_warning=scan_warning,
        abuse_warnings=abuse_warnings,
        routing=routing,
        pii_result=pii_result,
    )
