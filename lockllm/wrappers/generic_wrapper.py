"""Generic provider wrappers for OpenAI-compatible providers."""

from typing import Any, Optional

from ..errors import ConfigurationError
from ..types.common import ProxyOptions
from ..types.providers import UNIVERSAL_PROXY_URL
from ..utils import build_lockllm_headers, get_proxy_url


def _create_openai_compatible(
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
    is_async: bool = False,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Internal helper to create OpenAI-compatible clients.

    Args:
        provider: Provider name
        api_key: LockLLM API key
        base_url: Custom proxy URL
        is_async: Whether to create async client
        proxy_options: LockLLM proxy configuration
        **kwargs: Additional client options

    Returns:
        OpenAI or AsyncOpenAI client configured for provider

    Raises:
        ConfigurationError: If OpenAI SDK is not installed
    """
    try:
        import openai
    except ImportError:
        raise ConfigurationError(
            "OpenAI SDK not found. Install it with: pip install openai"
        )

    if proxy_options is not None:
        lockllm_headers = build_lockllm_headers(proxy_options)
        existing_headers = kwargs.get("default_headers") or {}
        existing_headers.update(lockllm_headers)
        kwargs["default_headers"] = existing_headers

    client_class = openai.AsyncOpenAI if is_async else openai.OpenAI
    proxy_url = base_url or get_proxy_url(provider)  # type: ignore

    return client_class(api_key=api_key, base_url=proxy_url, **kwargs)


# Universal proxy (non-BYOK, uses LockLLM credits)
def create_client(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create a client for LockLLM's universal proxy (synchronous).

    Uses LockLLM credits and supports 200+ models. No BYOK
    API key configuration required.

    Args:
        api_key: Your LockLLM API key
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy)
        proxy_options: LockLLM proxy configuration (scan mode,
            actions, routing, caching)
        **kwargs: Additional OpenAI client options

    Returns:
        OpenAI client configured to use LockLLM universal proxy

    Raises:
        ConfigurationError: If OpenAI SDK is not installed

    Example:
        >>> from lockllm import create_client, ProxyOptions
        >>> client = create_client(
        ...     api_key="...",
        ...     proxy_options=ProxyOptions(scan_action="block")
        ... )
        >>> response = client.chat.completions.create(
        ...     model="openai/gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    return _create_openai_compatible(
        "openai",
        api_key,
        base_url or UNIVERSAL_PROXY_URL,
        False,
        proxy_options,
        **kwargs,
    )


def create_async_client(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create an async client for LockLLM's universal proxy.

    Uses LockLLM credits and supports 200+ models. No BYOK
    API key configuration required.

    Args:
        api_key: Your LockLLM API key
        base_url: Custom proxy URL
            (default: https://api.lockllm.com/v1/proxy)
        proxy_options: LockLLM proxy configuration (scan mode,
            actions, routing, caching)
        **kwargs: Additional OpenAI client options

    Returns:
        AsyncOpenAI client configured to use LockLLM universal proxy

    Raises:
        ConfigurationError: If OpenAI SDK is not installed

    Example:
        >>> from lockllm import create_async_client, ProxyOptions
        >>> async def main():
        ...     client = create_async_client(
        ...         api_key="...",
        ...         proxy_options=ProxyOptions(scan_action="block")
        ...     )
        ...     response = await client.chat.completions.create(
        ...         model="openai/gpt-4",
        ...         messages=[{"role": "user", "content": "Hello!"}]
        ...     )
    """
    return _create_openai_compatible(
        "openai",
        api_key,
        base_url or UNIVERSAL_PROXY_URL,
        True,
        proxy_options,
        **kwargs,
    )


# Custom OpenAI-compatible endpoint
def create_openai_compatible(
    api_key: str,
    base_url: str,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create a client for any custom OpenAI-compatible endpoint (synchronous).

    Use this for custom provider endpoints that follow the OpenAI API
    format but aren't one of the 17 built-in providers.

    Args:
        api_key: Your LockLLM API key
        base_url: Full proxy URL for the custom endpoint (required)
        proxy_options: LockLLM proxy configuration (scan mode,
            actions, routing, caching)
        **kwargs: Additional OpenAI client options

    Returns:
        OpenAI client configured to use the custom endpoint

    Raises:
        ConfigurationError: If OpenAI SDK is not installed

    Example:
        >>> from lockllm import create_openai_compatible
        >>> client = create_openai_compatible(
        ...     api_key="...",
        ...     base_url="https://api.lockllm.com/v1/proxy/custom"
        ... )
    """
    return _create_openai_compatible(
        "openai", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_openai_compatible(
    api_key: str,
    base_url: str,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create an async client for any custom OpenAI-compatible endpoint.

    Use this for custom provider endpoints that follow the OpenAI API
    format but aren't one of the 17 built-in providers.

    Args:
        api_key: Your LockLLM API key
        base_url: Full proxy URL for the custom endpoint (required)
        proxy_options: LockLLM proxy configuration (scan mode,
            actions, routing, caching)
        **kwargs: Additional OpenAI client options

    Returns:
        AsyncOpenAI client configured to use the custom endpoint

    Raises:
        ConfigurationError: If OpenAI SDK is not installed

    Example:
        >>> from lockllm import create_async_openai_compatible
        >>> async def main():
        ...     client = create_async_openai_compatible(
        ...         api_key="...",
        ...         base_url="https://api.lockllm.com/v1/proxy/custom"
        ...     )
    """
    return _create_openai_compatible(
        "openai", api_key, base_url, True, proxy_options, **kwargs
    )


# Groq
def create_groq(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Groq client (OpenAI-compatible, synchronous).

    Example:
        >>> groq = create_groq(api_key="...")
        >>> response = groq.chat.completions.create(
        ...     model='llama-3.1-70b-versatile',
        ...     messages=[{'role': 'user', 'content': 'Hello!'}]
        ... )
    """
    return _create_openai_compatible(
        "groq", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_groq(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Groq client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "groq", api_key, base_url, True, proxy_options, **kwargs
    )


# DeepSeek
def create_deepseek(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create DeepSeek client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "deepseek", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_deepseek(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async DeepSeek client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "deepseek", api_key, base_url, True, proxy_options, **kwargs
    )


# Mistral
def create_mistral(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Mistral AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "mistral", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_mistral(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Mistral AI client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "mistral", api_key, base_url, True, proxy_options, **kwargs
    )


# Perplexity
def create_perplexity(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Perplexity client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "perplexity", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_perplexity(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Perplexity client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "perplexity", api_key, base_url, True, proxy_options, **kwargs
    )


# OpenRouter
def create_openrouter(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create OpenRouter client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "openrouter", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_openrouter(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async OpenRouter client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "openrouter", api_key, base_url, True, proxy_options, **kwargs
    )


# Together
def create_together(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Together AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "together", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_together(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Together AI client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "together", api_key, base_url, True, proxy_options, **kwargs
    )


# xAI
def create_xai(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create xAI (Grok) client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "xai", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_xai(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async xAI (Grok) client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "xai", api_key, base_url, True, proxy_options, **kwargs
    )


# Fireworks
def create_fireworks(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Fireworks AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "fireworks", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_fireworks(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Fireworks AI client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "fireworks", api_key, base_url, True, proxy_options, **kwargs
    )


# Anyscale
def create_anyscale(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Anyscale client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "anyscale", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_anyscale(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Anyscale client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "anyscale", api_key, base_url, True, proxy_options, **kwargs
    )


# Hugging Face
def create_huggingface(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Hugging Face client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "huggingface", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_huggingface(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Hugging Face client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "huggingface", api_key, base_url, True, proxy_options, **kwargs
    )


# Gemini
def create_gemini(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Google Gemini client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "gemini", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_gemini(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Google Gemini client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "gemini", api_key, base_url, True, proxy_options, **kwargs
    )


# Cohere
def create_cohere(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Cohere client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "cohere", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_cohere(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Cohere client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "cohere", api_key, base_url, True, proxy_options, **kwargs
    )


# Azure
def create_azure(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Azure OpenAI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "azure", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_azure(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Azure OpenAI client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "azure", api_key, base_url, True, proxy_options, **kwargs
    )


# Bedrock
def create_bedrock(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create AWS Bedrock client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "bedrock", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_bedrock(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async AWS Bedrock client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "bedrock", api_key, base_url, True, proxy_options, **kwargs
    )


# Vertex AI
def create_vertex_ai(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create Google Vertex AI client (OpenAI-compatible, synchronous)."""
    return _create_openai_compatible(
        "vertex-ai", api_key, base_url, False, proxy_options, **kwargs
    )


def create_async_vertex_ai(
    api_key: str,
    base_url: Optional[str] = None,
    proxy_options: Optional[ProxyOptions] = None,
    **kwargs: Any,
) -> Any:
    """Create async Google Vertex AI client (OpenAI-compatible)."""
    return _create_openai_compatible(
        "vertex-ai", api_key, base_url, True, proxy_options, **kwargs
    )
