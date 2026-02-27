"""Scan request and response type definitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

# Sensitivity level type
Sensitivity = Literal["low", "medium", "high"]

# Scan mode type
ScanMode = Literal["normal", "policy_only", "combined"]

# Scan action type
ScanAction = Literal["block", "allow_with_warning"]

# Route action type
RouteAction = Literal["disabled", "auto", "custom"]

# PII action type
PIIAction = Literal["strip", "block", "allow_with_warning"]

# Compression action type
CompressionAction = Literal["toon", "compact", "combined"]


@dataclass
class ScanRequest:
    """Request to scan a prompt for security threats.

    Attributes:
        input: The text prompt to scan
        sensitivity: Detection threshold level (default: "medium")
            - "low": Fewer false positives, may miss sophisticated attacks
            - "medium": Balanced detection (recommended)
            - "high": Maximum protection, may have more false positives
    """

    input: str
    sensitivity: Sensitivity = "medium"


@dataclass
class ScanOptions:
    """Configuration options for scan requests.

    These options control which security checks are performed
    and how threats are handled.

    Attributes:
        scan_mode: Which security checks to perform
            - "normal": Core injection detection only
            - "policy_only": Custom policies only (skips core scan)
            - "combined": Both core + policies (default, maximum security)
        scan_action: Behavior when core injection is detected
            - "block": Block the request (raises PromptInjectionError)
            - "allow_with_warning": Allow with warning in response (default)
        policy_action: Behavior when custom policy violation is found
            - "block": Block the request (raises PolicyViolationError)
            - "allow_with_warning": Allow with warning in response (default)
        abuse_action: Behavior when abuse is detected (opt-in)
            - None: Abuse detection disabled (default)
            - "block": Block the request (raises AbuseDetectedError)
            - "allow_with_warning": Allow with warning in response
        chunk: Whether to enable chunking for long prompts
            - None: Use server default
            - True: Enable chunking
            - False: Disable chunking
        pii_action: PII detection behavior (opt-in)
            - None: PII detection disabled (default)
            - "strip": Strip PII entities from the prompt
            - "block": Block the request (raises PIIDetectedError)
            - "allow_with_warning": Allow with PII info in response
        compression: Prompt compression method (opt-in)
            - None: Disabled (default)
            - "toon": JSON-to-compact notation (free, JSON only)
            - "compact": ML-based compression ($0.0001/use, any text)
            - "combined": TOON then ML-based compression
                ($0.0001/use, maximum compression)
        compression_rate: Compression rate for compact/combined methods
            - None: Use server default (0.5)
            - Float between 0.3-0.7 (lower = more aggressive compression)
            - Only applies to "compact" and "combined" methods
    """

    scan_mode: Optional[ScanMode] = None
    scan_action: Optional[ScanAction] = None
    policy_action: Optional[ScanAction] = None
    abuse_action: Optional[ScanAction] = None
    chunk: Optional[bool] = None
    pii_action: Optional["PIIAction"] = None
    compression: Optional["CompressionAction"] = None
    compression_rate: Optional[float] = None


@dataclass
class PIIResult:
    """PII detection result from scan.

    Attributes:
        detected: Whether PII was detected
        entity_types: Types of PII entities found (user-friendly names)
        entity_count: Number of PII entities found
        redacted_input: Redacted input text (only present when pii_action is "strip")
    """

    detected: bool
    entity_types: List[str]
    entity_count: int
    redacted_input: Optional[str] = None


@dataclass
class CompressionResult:
    """Prompt compression result from scan.

    Attributes:
        method: Compression method used ("toon", "compact", or "combined")
        compressed_input: The compressed text
        original_length: Original text length in characters
        compressed_length: Compressed text length in characters
        compression_ratio: Ratio of compressed/original (lower = better)
    """

    method: str
    compressed_input: str
    original_length: int
    compressed_length: int
    compression_ratio: float


@dataclass
class Usage:
    """Usage statistics for the scan.

    Attributes:
        requests: Number of upstream inference requests used
        input_chars: Number of characters in the input
    """

    requests: int
    input_chars: int


@dataclass
class Debug:
    """Debug information (Pro plan only).

    Attributes:
        duration_ms: Total processing time in milliseconds
        inference_ms: ML inference time in milliseconds
        mode: Processing mode used ("single" or "chunked")
    """

    duration_ms: int
    inference_ms: int
    mode: Literal["single", "chunked"]


@dataclass
class ViolatedCategory:
    """A specific category violated within a policy.

    Attributes:
        name: Category name (e.g., "Violent Crimes", "Privacy")
        description: Detailed description of the category (optional)
    """

    name: str
    description: Optional[str] = None


@dataclass
class PolicyViolation:
    """A custom policy violation detected during scanning.

    Attributes:
        policy_name: Name of the violated policy
        violated_categories: List of violated category details
        violation_details: Specific text that triggered the violation
    """

    policy_name: str
    violated_categories: List[ViolatedCategory]
    violation_details: Optional[str] = None


@dataclass
class ScanWarning:
    """Warning for core injection detection (allow_with_warning mode).

    Attributes:
        message: Warning description
        injection_score: Injection risk score (0-100)
        confidence: Detection confidence (0-100)
        label: Binary classification (0=safe, 1=unsafe)
    """

    message: str
    injection_score: float
    confidence: float
    label: int


@dataclass
class AbuseWarning:
    """Warning for detected abuse patterns.

    Attributes:
        detected: Always True when present
        confidence: Overall abuse confidence (0-100)
        abuse_types: List of detected abuse types
        indicators: Detailed scores for each abuse category
        recommendation: Suggested mitigation action
    """

    detected: bool
    confidence: float
    abuse_types: List[str]
    indicators: Dict[str, float]
    recommendation: Optional[str] = None


@dataclass
class RoutingInfo:
    """Smart routing metadata.

    Attributes:
        enabled: Whether routing was applied
        task_type: Detected task classification
        complexity: Complexity score (0-1)
        selected_model: Model chosen by router
        reasoning: Why this model was selected
        estimated_cost: Estimated API cost for the request
    """

    enabled: bool
    task_type: str
    complexity: float
    selected_model: Optional[str] = None
    reasoning: Optional[str] = None
    estimated_cost: Optional[float] = None


@dataclass
class ScanResult:
    """Core scan result data.

    Attributes:
        safe: Whether the input is safe (True) or malicious (False)
        label: Binary classification (0=safe, 1=malicious)
        confidence: Confidence score (0-100), None in policy_only mode
        injection: Injection risk score (0-100), None in policy_only mode
        sensitivity: Sensitivity level used for the scan
    """

    safe: bool
    label: Literal[0, 1]
    confidence: Optional[float]
    injection: Optional[float]
    sensitivity: Sensitivity


@dataclass
class ScanResponse(ScanResult):
    """Complete scan response from the API.

    Attributes:
        request_id: Unique request identifier for tracking
        usage: Usage statistics
        debug: Debug information (Pro plan only, optional)
        policy_confidence: Policy check confidence (0-100),
            present in policy_only and combined modes
        policy_warnings: List of custom policy violations
            (when action is allow_with_warning)
        scan_warning: Core injection warning details
            (when action is allow_with_warning)
        abuse_warnings: Abuse detection results
            (when abuse detection is enabled)
        routing: Smart routing metadata
            (when routing is enabled)
        pii_result: PII detection result
            (when PII detection is enabled)
        compression_result: Prompt compression result
            (when compression is enabled)
    """

    request_id: str = ""
    usage: Usage = field(default_factory=lambda: Usage(requests=0, input_chars=0))
    debug: Optional[Debug] = None
    policy_confidence: Optional[float] = None
    policy_warnings: Optional[List[PolicyViolation]] = None
    scan_warning: Optional[ScanWarning] = None
    abuse_warnings: Optional[AbuseWarning] = None
    routing: Optional[RoutingInfo] = None
    pii_result: Optional[PIIResult] = None
    compression_result: Optional[CompressionResult] = None
