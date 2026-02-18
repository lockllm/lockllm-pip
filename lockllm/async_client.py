"""Main asynchronous LockLLM client."""

from typing import Any, Optional

from .async_http_client import AsyncHttpClient
from .async_scan import AsyncScanClient
from .errors import ConfigurationError
from .types.common import LockLLMConfig
from .types.scan import ScanAction, ScanMode, ScanOptions, ScanResponse, Sensitivity

DEFAULT_BASE_URL = "https://api.lockllm.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3


class AsyncLockLLM:
    """Main LockLLM client for AI security scanning (asynchronous).

    This is the async version of the LockLLM client. It provides async methods
    to scan prompts for security threats such as prompt injection, jailbreak
    attempts, and other adversarial attacks.

    Args:
        api_key: Your LockLLM API key from
            https://www.lockllm.com/dashboard
        base_url: Custom base URL (default: https://api.lockllm.com)
        timeout: Request timeout in seconds (default: 60.0)
        max_retries: Maximum retry attempts (default: 3)

    Raises:
        ConfigurationError: If API key is missing or invalid

    Example:
        >>> import asyncio
        >>> async def main():
        ...     lockllm = AsyncLockLLM(api_key="...")
        ...     result = await lockllm.scan(
        ...         input="Ignore previous instructions"
        ...     )
        ...     if not result.safe:
        ...         print(f"Malicious! {result.injection}%")
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """Initialize the async LockLLM client.

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

        self._http = AsyncHttpClient(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )

        self._scan_client = AsyncScanClient(self._http)

    async def scan(
        self,
        input: str,
        sensitivity: Sensitivity = "medium",
        scan_mode: Optional[ScanMode] = None,
        scan_action: Optional[ScanAction] = None,
        policy_action: Optional[ScanAction] = None,
        abuse_action: Optional[ScanAction] = None,
        chunk: Optional[bool] = None,
        scan_options: Optional[ScanOptions] = None,
        **options: Any,
    ) -> ScanResponse:
        """Scan a prompt for security threats (async).

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
            InsufficientCreditsError: If credit balance is too low

        Example:
            >>> result = await lockllm.scan(
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
            >>> result = await lockllm.scan(input="test", scan_options=opts)
        """
        return await self._scan_client.scan(
            input=input,
            sensitivity=sensitivity,
            scan_mode=scan_mode,
            scan_action=scan_action,
            policy_action=policy_action,
            abuse_action=abuse_action,
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

    async def close(self) -> None:
        """Close the HTTP client and release resources.

        It's recommended to call this when you're done using the client,
        or use the client as an async context manager.
        """
        await self._http.close()

    async def __aenter__(self) -> "AsyncLockLLM":
        """Async context manager entry.

        Example:
            >>> async with AsyncLockLLM(api_key="...") as client:
            ...     result = await client.scan(input="Hello")
        """
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
