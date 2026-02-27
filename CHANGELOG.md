# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-02-27

### Added

#### Prompt Compression
Reduce token usage and save costs by compressing prompts before sending them to AI providers. Two compression methods are available:

- **`toon`** (Free) - JSON-to-compact notation. Converts structured JSON content into a compressed shorthand format. Lossless and completely free.
- **`compact`** (Charged) - ML-based compression. Works on any text format with configurable compression rate. Costs $0.0001 per use.
- **`combined`** (Charged) - TOON first, then ML-based compression on the output. Maximum compression. Costs $0.0001 per use.

Configure compression rate for the `compact` and `combined` methods with `compression_rate` (0.3-0.7, default 0.5). Lower values compress more aggressively.

```python
from lockllm import LockLLM

lockllm = LockLLM(api_key="your-lockllm-key")

# Free JSON-to-compact compression
result = lockllm.scan(
    input='{"name": "John", "age": 30, "city": "NYC"}',
    compression="toon",
)

if result.compression_result:
    print(result.compression_result.compressed_input)
    print(result.compression_result.compression_ratio)  # e.g. 0.65

# ML-based compression with custom rate
result = lockllm.scan(
    input="A very long prompt that needs compression...",
    compression="compact",
    compression_rate=0.4,  # More aggressive compression
)
```

#### Compression via Proxy Wrappers
Compression is also available through all proxy wrappers via `ProxyOptions`:

```python
from lockllm import create_openai, ProxyOptions

openai = create_openai(
    api_key="your-lockllm-key",
    proxy_options=ProxyOptions(compression="toon")
)
```

#### Compression via ScanOptions
Use `ScanOptions` for reusable compression configurations:

```python
from lockllm import ScanOptions

opts = ScanOptions(compression="compact", compression_rate=0.5)
result = lockllm.scan(input=user_prompt, scan_options=opts)
```

#### New Type Exports
- `CompressionAction` - Literal type for compression methods (`"toon"` | `"compact"` | `"combined"`)
- `CompressionResult` - Dataclass with `method`, `compressed_input`, `original_length`, `compressed_length`, `compression_ratio`
- `ProxyCompressionMetadata` - Metadata from proxy response headers

### Notes
- Compression is opt-in. Existing integrations continue to work without any changes.
- TOON compression is free. Compact compression costs $0.0001 per use.

---

## [1.2.0] - 2026-02-21

### Added

#### PII Detection and Redaction
Protect sensitive personal information in prompts before they reach AI providers. When enabled, LockLLM detects emails, phone numbers, SSNs, credit card numbers, and other PII entities. Choose how to handle detected PII with the `pii_action` option:

- **`block`** - Reject requests containing PII entirely. Raises a `PIIDetectedError` with entity types and count.
- **`strip`** - Automatically redact PII from prompts before forwarding to the AI provider. The redacted text is available via `redacted_input` in the scan response.
- **`allow_with_warning`** - Allow requests through but include PII metadata in the response for logging.

PII detection is opt-in and disabled by default.

```python
from lockllm import create_openai, ProxyOptions, PIIDetectedError

# Strip PII automatically before sending to AI
openai = create_openai(
    api_key="your-lockllm-key",
    proxy_options=ProxyOptions(pii_action="strip")
)

# Or block requests containing PII
try:
    openai.chat.completions.create(...)
except PIIDetectedError as e:
    print(e.entity_types)   # ['email', 'phone_number']
    print(e.entity_count)   # 3
```

#### Scan API PII Support
The scan endpoint now accepts a `pii_action` option alongside existing scan options:

```python
result = lockllm.scan(
    input="My email is test@example.com",
    pii_action="block",
    scan_action="block",
)

if result.pii_result:
    print(result.pii_result.detected)        # True
    print(result.pii_result.entity_types)     # ['email']
    print(result.pii_result.entity_count)     # 1
    print(result.pii_result.redacted_input)   # 'My email is [EMAIL]' (strip mode only)
```

#### Universal Proxy Client
Access 200+ models through LockLLM's universal proxy without configuring individual provider API keys. Uses LockLLM credits for billing - no BYOK setup required.

```python
from lockllm import create_client, ProxyOptions

client = create_client(
    api_key="your-lockllm-key",
    proxy_options=ProxyOptions(scan_action="block")
)

response = client.chat.completions.create(
    model="openai/gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Both sync (`create_client`) and async (`create_async_client`) variants are available.

#### Custom OpenAI-Compatible Endpoints
Connect to any custom endpoint that follows the OpenAI API format but isn't one of the 17+ built-in providers. Useful for self-hosted models or niche providers.

```python
from lockllm import create_openai_compatible

client = create_openai_compatible(
    api_key="your-lockllm-key",
    base_url="https://api.lockllm.com/v1/proxy/custom"
)
```

Both sync (`create_openai_compatible`) and async (`create_async_openai_compatible`) variants are available.

#### Enhanced Proxy Response Metadata
Proxy responses now include additional fields for better observability:

- **PII detection metadata** - `pii_detected` object with detection status, entity types, count, and action taken
- **Sensitivity and label** - `sensitivity` level used and numeric `label` (0 = safe, 1 = unsafe)
- **Decoded detail fields** - `scan_detail`, `policy_detail`, and `abuse_detail` automatically decoded from base64 response headers
- **Extended routing metadata** - `estimated_original_cost`, `estimated_routed_cost`, `estimated_input_tokens`, `estimated_output_tokens`, and `routing_fee_reason`

### Notes
- PII detection is opt-in. Existing integrations continue to work without any changes.
- All new types (`PIIAction`, `PIIResult`, `PIIDetectedError`, `ProxyPIIDetected`) are fully exported for type checking.

---

## [1.1.0] - 2026-02-18

### Added

#### Custom Content Policy Enforcement
You can now enforce your own content rules on top of LockLLM's built-in security. Create custom policies in the [dashboard](https://www.lockllm.com/policies), and the SDK will automatically check prompts against them. When a policy is violated, you'll get a `PolicyViolationError` with the exact policy name, violated categories, and details.

```python
from lockllm import create_openai, PolicyViolationError

try:
    openai.chat.completions.create(...)
except PolicyViolationError as e:
    print(e.violated_policies)
    # [{"policy_name": "No competitor mentions", "violated_categories": [...]}]
```

#### AI Abuse Detection
Protect your endpoints from automated misuse. When enabled, LockLLM detects bot-generated content, repetitive prompts, and resource exhaustion attacks. If abuse is detected, you'll get an `AbuseDetectedError` with confidence scores and detailed indicator breakdowns.

```python
from lockllm import create_openai, ProxyOptions

openai = create_openai(
    api_key=os.getenv("LOCKLLM_API_KEY"),
    proxy_options=ProxyOptions(abuse_action="block")
)
```

#### Credit Balance Awareness
The SDK now returns a dedicated `InsufficientCreditsError` when your balance is too low for a request. The error includes your `current_balance` and the `estimated_cost`, so you can handle billing gracefully in your application.

#### Scan Modes and Actions
Control exactly what gets checked and what happens when threats are found:

- **Scan modes** - Choose `normal` (core security only), `policy_only` (custom policies only), or `combined` (both)
- **Actions per detection type** - Set `block` or `allow_with_warning` independently for core scans, custom policies, and abuse detection
- **Abuse detection** is opt-in - disabled by default, enable it with `abuse_action`

```python
result = lockllm.scan(
    input=user_prompt,
    scan_mode="combined",
    sensitivity="high",
    scan_action="block",
    policy_action="allow_with_warning",
    abuse_action="block",
)
```

You can also use the `ScanOptions` dataclass for reusable configurations:

```python
from lockllm import ScanOptions

opts = ScanOptions(scan_mode="combined", scan_action="block")
result = lockllm.scan(input=user_prompt, scan_options=opts)
```

#### Proxy Options on All Wrappers
All wrapper functions (`create_openai`, `create_anthropic`, `create_groq`, etc. and their `create_async_*` variants) now accept a `proxy_options` parameter so you can configure security behavior at initialization time:

```python
from lockllm import create_openai, ProxyOptions

openai = create_openai(
    api_key=os.getenv("LOCKLLM_API_KEY"),
    proxy_options=ProxyOptions(
        scan_mode="combined",
        scan_action="block",
        policy_action="block",
        route_action="auto",
        cache_response=True,
        cache_ttl=3600,
    )
)
```

#### Intelligent Routing
Let LockLLM automatically select the best model for each request based on task type and complexity. Set `route_action="auto"` to enable, or `route_action="custom"` to use your own routing rules from the dashboard.

#### Response Caching
Reduce costs by caching identical LLM responses. Enabled by default in proxy mode - disable it with `cache_response=False` or customize the TTL with `cache_ttl`.

#### Universal Proxy Mode
Access 200+ models without configuring individual provider API keys using `get_universal_proxy_url()`. Uses LockLLM credits instead of BYOK.

```python
from lockllm import get_universal_proxy_url
url = get_universal_proxy_url()
# 'https://api.lockllm.com/v1/proxy'
```

#### Proxy Response Metadata
New utilities to read detailed metadata from proxy responses - scan results, routing decisions, cache status, and credit usage:

```python
from lockllm import parse_proxy_metadata
metadata = parse_proxy_metadata(response_headers)
# metadata.safe, metadata.routing, metadata.cache_status, metadata.credits_deducted, etc.
```

#### Expanded Scan Response
Scan responses now include richer data when using advanced features:
- `policy_warnings` - Which custom policies were violated and why
- `scan_warning` - Injection details when using `allow_with_warning`
- `abuse_warnings` - Abuse indicators when abuse detection is enabled
- `routing` - Task type, complexity score, and selected model when routing is enabled
- `policy_confidence` - Separate confidence score for policy checks

#### New Type Exports
- `ProxyOptions` - Configuration dataclass for proxy wrapper options
- `ProxyResponseMetadata` - Typed dataclass for parsed proxy response metadata
- `ScanOptions`, `ScanMode`, `ScanAction`, `RouteAction` - Scan configuration types
- `PolicyViolation`, `ViolatedCategory`, `ScanWarning`, `AbuseWarning`, `RoutingInfo` - Scan response types
- `TaskType`, `ComplexityTier` - Routing type aliases

### Changed
- The scan API is fully backward compatible - existing code works without changes. Internally, scan configuration is now sent via HTTP headers for better compatibility and caching behavior.
- `ScanResult.confidence` and `ScanResult.injection` are now `Optional[float]` (they are `None` in `policy_only` mode where core injection scanning is skipped).

### Notes
- All new features are opt-in. Existing integrations continue to work without any changes.
- Custom policies, abuse detection, and routing are configured in the [LockLLM dashboard](https://www.lockllm.com/dashboard).

---

## [1.0.0] - 2025-01-17

### Added
- Initial release of LockLLM Python SDK
- Synchronous API with `LockLLM` class
- Asynchronous API with `AsyncLockLLM` class
- Direct scan API for manual validation
- Provider wrappers for 17 AI providers:
  - OpenAI
  - Anthropic
  - Groq
  - DeepSeek
  - Mistral AI
  - Perplexity
  - OpenRouter
  - Together AI
  - xAI (Grok)
  - Fireworks AI
  - Anyscale
  - Hugging Face
  - Google Gemini
  - Cohere
  - Azure OpenAI
  - AWS Bedrock
  - Google Vertex AI
- Both sync and async wrappers for all providers
- Comprehensive error handling with 7 custom exceptions
- Automatic retry with exponential backoff
- Rate limit handling with Retry-After support
- Full type hints with mypy support
- Context manager support for resource cleanup
- Configurable sensitivity levels (low/medium/high)
- Request ID tracking for debugging
- Usage statistics and debug information
- Comprehensive documentation and examples

### Features
- Prompt injection detection
- Jailbreak prevention
- System prompt extraction defense
- Instruction override detection
- Agent & tool abuse protection
- RAG & document injection scanning
- Indirect injection detection
- Evasion & obfuscation detection

[1.0.0]: https://github.com/lockllm/lockllm-pip/releases/tag/v1.0.0
