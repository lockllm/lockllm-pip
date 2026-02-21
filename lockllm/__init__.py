"""LockLLM Python SDK - Enterprise-grade AI security for LLM apps.

LockLLM provides real-time prompt injection and jailbreak detection
across 17+ LLM providers with both synchronous and asynchronous APIs.

Basic usage:
    >>> from lockllm import LockLLM
    >>> lockllm = LockLLM(api_key="...")
    >>> result = lockllm.scan(input="Ignore previous instructions")
    >>> if not result.safe:
    ...     print(f"Malicious prompt detected: {result.injection}%")

Async usage:
    >>> from lockllm import AsyncLockLLM
    >>> async def main():
    ...     lockllm = AsyncLockLLM(api_key="...")
    ...     result = await lockllm.scan(
    ...         input="Ignore previous instructions"
    ...     )
    ...     if not result.safe:
    ...         print(f"Malicious prompt detected: {result.injection}%")

Provider wrappers:
    >>> from lockllm import create_openai
    >>> openai = create_openai(api_key="...")
    >>> response = openai.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "Hello!"}]
    ... )

With proxy options:
    >>> from lockllm import create_openai, ProxyOptions
    >>> openai = create_openai(
    ...     api_key="...",
    ...     proxy_options=ProxyOptions(
    ...         scan_action="block",
    ...         route_action="auto"
    ...     )
    ... )

Scan with modes:
    >>> result = lockllm.scan(
    ...     input="test",
    ...     scan_mode="combined",
    ...     scan_action="block",
    ...     policy_action="block"
    ... )
"""

from ._version import __version__

# Main clients
from .async_client import AsyncLockLLM
from .client import LockLLM

# Errors
from .errors import (
    AbuseDetectedError,
    AuthenticationError,
    ConfigurationError,
    InsufficientCreditsError,
    LockLLMError,
    NetworkError,
    PIIDetectedError,
    PolicyViolationError,
    PromptInjectionError,
    RateLimitError,
    UpstreamError,
)

# Types - common
from .types.common import (
    LockLLMConfig,
    ProxyAbuseDetected,
    ProxyOptions,
    ProxyPIIDetected,
    ProxyPolicyWarnings,
    ProxyResponseMetadata,
    ProxyRoutingMetadata,
    ProxyScanWarning,
    RequestOptions,
)

# Types - providers
from .types.providers import (
    PROVIDER_BASE_URLS,
    UNIVERSAL_PROXY_URL,
    ComplexityTier,
    ProviderName,
    TaskType,
)

# Types - scan
from .types.scan import (
    AbuseWarning,
    Debug,
    PIIAction,
    PIIResult,
    PolicyViolation,
    RouteAction,
    RoutingInfo,
    ScanAction,
    ScanMode,
    ScanOptions,
    ScanRequest,
    ScanResponse,
    ScanResult,
    ScanWarning,
    Sensitivity,
    Usage,
    ViolatedCategory,
)

# Utilities
from .utils import (
    build_lockllm_headers,
    decode_detail_field,
    get_all_proxy_urls,
    get_proxy_url,
    get_universal_proxy_url,
    parse_proxy_metadata,
)

# Provider wrappers
from .wrappers import (
    create_anthropic,
    create_anyscale,
    create_async_anthropic,
    create_async_anyscale,
    create_async_azure,
    create_async_bedrock,
    create_async_cohere,
    create_async_deepseek,
    create_async_fireworks,
    create_async_gemini,
    create_async_groq,
    create_async_huggingface,
    create_async_mistral,
    create_async_openai,
    create_async_openrouter,
    create_async_perplexity,
    create_async_together,
    create_async_vertex_ai,
    create_async_xai,
    create_azure,
    create_bedrock,
    create_cohere,
    create_deepseek,
    create_fireworks,
    create_gemini,
    create_groq,
    create_huggingface,
    create_mistral,
    create_openai,
    create_openrouter,
    create_perplexity,
    create_together,
    create_vertex_ai,
    create_xai,
)

__all__ = [
    # Version
    "__version__",
    # Main clients
    "LockLLM",
    "AsyncLockLLM",
    # Errors
    "LockLLMError",
    "AuthenticationError",
    "RateLimitError",
    "PromptInjectionError",
    "PolicyViolationError",
    "AbuseDetectedError",
    "PIIDetectedError",
    "InsufficientCreditsError",
    "UpstreamError",
    "ConfigurationError",
    "NetworkError",
    # Types - common
    "LockLLMConfig",
    "RequestOptions",
    "ProxyOptions",
    "ProxyResponseMetadata",
    "ProxyScanWarning",
    "ProxyPolicyWarnings",
    "ProxyAbuseDetected",
    "ProxyPIIDetected",
    "ProxyRoutingMetadata",
    # Types - providers
    "ProviderName",
    "PROVIDER_BASE_URLS",
    "UNIVERSAL_PROXY_URL",
    "TaskType",
    "ComplexityTier",
    # Types - scan
    "ScanRequest",
    "ScanResponse",
    "ScanResult",
    "ScanOptions",
    "ScanMode",
    "ScanAction",
    "RouteAction",
    "PIIAction",
    "PIIResult",
    "PolicyViolation",
    "ViolatedCategory",
    "ScanWarning",
    "AbuseWarning",
    "RoutingInfo",
    "Usage",
    "Debug",
    "Sensitivity",
    # Utilities
    "get_proxy_url",
    "get_all_proxy_urls",
    "get_universal_proxy_url",
    "build_lockllm_headers",
    "parse_proxy_metadata",
    "decode_detail_field",
    # Provider wrappers - OpenAI
    "create_openai",
    "create_async_openai",
    # Anthropic
    "create_anthropic",
    "create_async_anthropic",
    # Groq
    "create_groq",
    "create_async_groq",
    # DeepSeek
    "create_deepseek",
    "create_async_deepseek",
    # Mistral
    "create_mistral",
    "create_async_mistral",
    # Perplexity
    "create_perplexity",
    "create_async_perplexity",
    # OpenRouter
    "create_openrouter",
    "create_async_openrouter",
    # Together
    "create_together",
    "create_async_together",
    # xAI
    "create_xai",
    "create_async_xai",
    # Fireworks
    "create_fireworks",
    "create_async_fireworks",
    # Anyscale
    "create_anyscale",
    "create_async_anyscale",
    # Hugging Face
    "create_huggingface",
    "create_async_huggingface",
    # Gemini
    "create_gemini",
    "create_async_gemini",
    # Cohere
    "create_cohere",
    "create_async_cohere",
    # Azure
    "create_azure",
    "create_async_azure",
    # Bedrock
    "create_bedrock",
    "create_async_bedrock",
    # Vertex AI
    "create_vertex_ai",
    "create_async_vertex_ai",
]
