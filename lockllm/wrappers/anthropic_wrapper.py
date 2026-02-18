"""Anthropic provider wrappers."""

from typing import Any, Optional

from ..errors import ConfigurationError
from ..types.common import ProxyOptions
from ..utils import build_lockllm_headers, get_proxy_url


def create_anthropic(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Anthropic client with LockLLM proxy (synchronous).

    Drop-in replacement for Anthropic client initialization. All requests
    are automatically scanned by LockLLM before being forwarded to Anthropic.

    Args:
        api_key: Your LockLLM API key (not your Anthropic key)
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy/anthropic)
        proxy_options: LockLLM proxy configuration (scan mode,
            actions, routing, caching)
        **kwargs: Additional Anthropic client options

    Returns:
        Anthropic client configured to use LockLLM proxy

    Raises:
        ConfigurationError: If Anthropic SDK is not installed

    Example:
        >>> from lockllm import create_anthropic, ProxyOptions
        >>> anthropic = create_anthropic(
        ...     api_key="...",
        ...     proxy_options=ProxyOptions(scan_action="block")
        ... )
        >>> message = anthropic.messages.create(
        ...     model="claude-sonnet-4-5-20250929",
        ...     max_tokens=1024,
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    try:
        import anthropic
    except ImportError:
        raise ConfigurationError(
            "Anthropic SDK not found. Install it with: pip install anthropic"
        )

    if proxy_options is not None:
        lockllm_headers = build_lockllm_headers(proxy_options)
        existing_headers = kwargs.get("default_headers") or {}
        existing_headers.update(lockllm_headers)
        kwargs["default_headers"] = existing_headers

    return anthropic.Anthropic(
        api_key=api_key, base_url=base_url or get_proxy_url("anthropic"), **kwargs
    )


def create_async_anthropic(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Anthropic client with LockLLM proxy.

    Drop-in replacement for AsyncAnthropic client initialization. All requests
    are automatically scanned by LockLLM before being forwarded to Anthropic.

    Args:
        api_key: Your LockLLM API key (not your Anthropic key)
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy/anthropic)
        proxy_options: LockLLM proxy configuration (scan mode,
            actions, routing, caching)
        **kwargs: Additional Anthropic client options

    Returns:
        AsyncAnthropic client configured to use LockLLM proxy

    Raises:
        ConfigurationError: If Anthropic SDK is not installed

    Example:
        >>> from lockllm import create_async_anthropic, ProxyOptions
        >>> async def main():
        ...     anthropic = create_async_anthropic(
        ...         api_key="...",
        ...         proxy_options=ProxyOptions(scan_action="block")
        ...     )
        ...     message = await anthropic.messages.create(
        ...         model="claude-sonnet-4-5-20250929",
        ...         max_tokens=1024,
        ...         messages=[{"role": "user", "content": "Hello!"}]
        ...     )
    """
    try:
        import anthropic
    except ImportError:
        raise ConfigurationError(
            "Anthropic SDK not found. Install it with: pip install anthropic"
        )

    if proxy_options is not None:
        lockllm_headers = build_lockllm_headers(proxy_options)
        existing_headers = kwargs.get("default_headers") or {}
        existing_headers.update(lockllm_headers)
        kwargs["default_headers"] = existing_headers

    return anthropic.AsyncAnthropic(
        api_key=api_key, base_url=base_url or get_proxy_url("anthropic"), **kwargs
    )
