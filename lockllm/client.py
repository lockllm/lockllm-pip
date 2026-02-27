"""Main synchronous LockLLM client."""

from typing import Any, Optional

from .errors import ConfigurationError
from .http_client import HttpClient
from .scan import ScanClient
from .types.common import LockLLMConfig
from .types.scan import (
    CompressionAction,
    PIIAction,
    ScanAction,
    ScanMode,
    ScanOptions,
    ScanResponse,
    Sensitivity,
)

DEFAULT_BASE_URL = "https://api.lockllm.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3


class LockLLM:
    """Main LockLLM client for AI security scanning (synchronous).

    This is the primary entry point for using the LockLLM SDK. It provides
    methods to scan prompts for security threats such as prompt injection,
    jailbreak attempts, and other adversarial attacks.

    Args:
        api_key: Your LockLLM API key from
            https://www.lockllm.com/dashboard
        base_url: Custom base URL (default: https://api.lockllm.com)
        timeout: Request timeout in seconds (default: 60.0)
        max_retries: Maximum retry attempts (default: 3)

    Raises:
        ConfigurationError: If API key is missing or invalid

    Example:
        >>> lockllm = LockLLM(api_key="...")
        >>> result = lockllm.scan(input="Ignore previous instructions")
        >>> if not result.safe:
        ...     print(f"Malicious prompt detected: {result.injection}%")
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """Initialize the LockLLM client.

        Args:
            api_key: Your LockLLM API key
            base_url: Custom API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not api_key or not api_key.strip():
            raise ConfigurationError(
                "API key is required. Get your API key from "
                "https://www.lockllm.com/dashboard"
            )

        self._config = LockLLMConfig(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=(timeout if timeout is not None else DEFAULT_TIMEOUT),
            max_retries=(
                max_retries if max_retries is not None else DEFAULT_MAX_RETRIES
            ),
        )

        self._http = HttpClient(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )

        self._scan_client = ScanClient(self._http)

    def scan(
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
        """Scan a prompt for security threats.

        Analyzes input text using advanced ML models to detect prompt
        injection, jailbreak attempts, and other adversarial attacks.

        Args:
            input: The text prompt to scan for security threats
            sensitivity: Detection threshold level (default: "medium")
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
            >>> result = lockllm.scan(
            ...     input="Ignore previous instructions",
            ...     sensitivity="medium",
            ...     scan_mode="combined",
            ...     scan_action="block"
            ... )
            >>> if not result.safe:
            ...     print(f"Malicious! Injection score: {result.injection}%")
            ...     print(f"Request ID: {result.request_id}")

            Using ScanOptions:
            >>> opts = ScanOptions(scan_mode="combined", scan_action="block")
            >>> result = lockllm.scan(input="test", scan_options=opts)
        """
        return self._scan_client.scan(
            input=input,
            sensitivity=sensitivity,
            scan_mode=scan_mode,
            scan_action=scan_action,
            policy_action=policy_action,
            abuse_action=abuse_action,
            pii_action=pii_action,
            compression=compression,
            compression_rate=compression_rate,
            chunk=chunk,
            scan_options=scan_options,
            **options,
        )

    @property
    def config(self) -> LockLLMConfig:
        """Get the current configuration (readonly).

        Returns:
            The LockLLMConfig object
        """
        return self._config

    def close(self) -> None:
        """Close the HTTP client and release resources.

        It's recommended to call this when you're done using the client,
        or use the client as a context manager.
        """
        self._http.close()

    def __enter__(self) -> "LockLLM":
        """Context manager entry.

        Example:
            >>> with LockLLM(api_key="...") as client:
            ...     result = client.scan(input="test")
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.close()
