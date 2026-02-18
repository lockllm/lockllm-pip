"""Tests for synchronous scan client."""

from unittest.mock import Mock, patch

import pytest

from lockllm.http_client import HttpClient
from lockllm.scan import ScanClient, _build_scan_headers, _parse_scan_response
from lockllm.types.scan import ScanOptions, ScanResponse


class TestScanClient:
    """Tests for ScanClient."""

    def test_initialization(self, api_key):
        """Test scan client initialization."""
        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        assert scan_client._http == http

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_success(self, mock_post, api_key, mock_scan_response):
        """Test successful scan."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(input="test prompt", sensitivity="medium")

        assert isinstance(result, ScanResponse)
        assert result.safe is True
        assert result.confidence == 95
        assert result.injection == 2
        assert result.request_id == "test_request_123"
        assert result.usage.requests == 1
        assert result.usage.input_chars == 25

        # Verify HTTP client was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/v1/scan"
        assert call_args[1]["body"]["input"] == "test prompt"
        assert call_args[1]["body"]["sensitivity"] == "medium"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_with_debug_info(self, mock_post, api_key, mock_unsafe_scan_response):
        """Test scan with debug information."""
        mock_post.return_value = (mock_unsafe_scan_response, "test_request_456")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(input="malicious prompt", sensitivity="high")

        assert isinstance(result, ScanResponse)
        assert result.safe is False
        assert result.label == 1
        assert result.injection == 87
        assert result.debug is not None
        assert result.debug.duration_ms == 150
        assert result.debug.inference_ms == 120
        assert result.debug.mode == "single"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_with_custom_options(self, mock_post, api_key, mock_scan_response):
        """Test scan with custom options."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(
            input="test",
            sensitivity="low",
            headers={"X-Custom": "value"},
            timeout=15.0,
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["headers"]["X-Custom"] == "value"
        assert call_args[1]["headers"]["X-LockLLM-Sensitivity"] == "low"
        assert call_args[1]["timeout"] == 15.0

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_default_sensitivity(self, mock_post, api_key, mock_scan_response):
        """Test scan with default sensitivity."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(input="test prompt")

        call_args = mock_post.call_args
        assert call_args[1]["body"]["sensitivity"] == "medium"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_with_scan_options(self, mock_post, api_key, mock_scan_response):
        """Test scan with ScanOptions object."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        opts = ScanOptions(
            scan_mode="combined",
            scan_action="block",
            policy_action="allow_with_warning",
            abuse_action="block",
            chunk=True,
        )
        result = scan_client.scan(input="test", scan_options=opts)

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "allow_with_warning"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Chunk"] == "true"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_kwargs_override_scan_options(self, mock_post, api_key, mock_scan_response):
        """Test that individual kwargs take precedence over ScanOptions."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        opts = ScanOptions(
            scan_mode="normal",
            scan_action="allow_with_warning",
            policy_action="allow_with_warning",
            abuse_action="allow_with_warning",
            chunk=False,
        )
        result = scan_client.scan(
            input="test",
            scan_options=opts,
            scan_mode="combined",
            scan_action="block",
            policy_action="block",
            abuse_action="block",
            chunk=True,
        )

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "block"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Chunk"] == "true"

    @patch("lockllm.http_client.HttpClient.post")
    def test_scan_with_all_header_options(self, mock_post, api_key, mock_scan_response):
        """Test scan with all header-producing options."""
        mock_post.return_value = (mock_scan_response, "test_request_123")

        http = HttpClient(base_url="https://api.lockllm.com", api_key=api_key)
        scan_client = ScanClient(http)

        result = scan_client.scan(
            input="test",
            scan_mode="combined",
            scan_action="block",
            policy_action="block",
            abuse_action="allow_with_warning",
            chunk=True,
            sensitivity="high",
        )

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "block"
        assert headers["X-LockLLM-Abuse-Action"] == "allow_with_warning"
        assert headers["X-LockLLM-Chunk"] == "true"
        assert headers["X-LockLLM-Sensitivity"] == "high"


class TestBuildScanHeaders:
    """Tests for _build_scan_headers helper."""

    def test_empty_headers(self):
        """Test building headers with no options."""
        headers = _build_scan_headers()
        assert headers == {}

    def test_all_headers(self):
        """Test building headers with all options."""
        headers = _build_scan_headers(
            scan_mode="combined",
            scan_action="block",
            policy_action="allow_with_warning",
            abuse_action="block",
            sensitivity="high",
            chunk=True,
        )
        assert headers["X-LockLLM-Scan-Mode"] == "combined"
        assert headers["X-LockLLM-Scan-Action"] == "block"
        assert headers["X-LockLLM-Policy-Action"] == "allow_with_warning"
        assert headers["X-LockLLM-Abuse-Action"] == "block"
        assert headers["X-LockLLM-Sensitivity"] == "high"
        assert headers["X-LockLLM-Chunk"] == "true"

    def test_chunk_false(self):
        """Test building headers with chunk=False."""
        headers = _build_scan_headers(chunk=False)
        assert headers["X-LockLLM-Chunk"] == "false"

    def test_partial_headers(self):
        """Test building headers with partial options."""
        headers = _build_scan_headers(scan_mode="normal", sensitivity="low")
        assert len(headers) == 2
        assert headers["X-LockLLM-Scan-Mode"] == "normal"
        assert headers["X-LockLLM-Sensitivity"] == "low"


class TestParseScanResponse:
    """Tests for _parse_scan_response."""

    def test_parse_basic_response(self):
        """Test parsing a basic scan response."""
        data = {
            "safe": True,
            "label": 0,
            "confidence": 95.0,
            "injection": 2.0,
            "sensitivity": "medium",
            "request_id": "req_123",
            "usage": {"requests": 1, "input_chars": 25},
        }
        result = _parse_scan_response(data, "req_fallback")

        assert result.safe is True
        assert result.label == 0
        assert result.confidence == 95.0
        assert result.injection == 2.0
        assert result.request_id == "req_123"
        assert result.usage.requests == 1

    def test_parse_response_with_policy_warnings(self):
        """Test parsing response with policy warnings."""
        data = {
            "safe": False,
            "label": 1,
            "confidence": 90.0,
            "injection": 5.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 50},
            "policy_warnings": [
                {
                    "policy_name": "No violence",
                    "violated_categories": [
                        {"name": "Violence", "description": "Violent content detected"},
                    ],
                    "violation_details": "Contains violent language",
                },
                {
                    "policy_name": "No hate speech",
                    "violated_categories": [
                        {"name": "Hate"},
                    ],
                },
            ],
        }
        result = _parse_scan_response(data, "req_123")

        assert result.policy_warnings is not None
        assert len(result.policy_warnings) == 2
        assert result.policy_warnings[0].policy_name == "No violence"
        assert len(result.policy_warnings[0].violated_categories) == 1
        assert result.policy_warnings[0].violated_categories[0].name == "Violence"
        assert result.policy_warnings[0].violated_categories[0].description == "Violent content detected"
        assert result.policy_warnings[0].violation_details == "Contains violent language"
        assert result.policy_warnings[1].violation_details is None

    def test_parse_response_with_scan_warning(self):
        """Test parsing response with scan warning."""
        data = {
            "safe": False,
            "label": 1,
            "confidence": 85.0,
            "injection": 80.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 30},
            "scan_warning": {
                "message": "Potential injection detected",
                "injection_score": 80,
                "confidence": 85,
                "label": 1,
            },
        }
        result = _parse_scan_response(data, "req_123")

        assert result.scan_warning is not None
        assert result.scan_warning.message == "Potential injection detected"
        assert result.scan_warning.injection_score == 80
        assert result.scan_warning.confidence == 85
        assert result.scan_warning.label == 1

    def test_parse_response_with_abuse_warnings(self):
        """Test parsing response with abuse warnings."""
        data = {
            "safe": False,
            "label": 1,
            "confidence": 70.0,
            "injection": 10.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 100},
            "abuse_warnings": {
                "detected": True,
                "confidence": 90,
                "abuse_types": ["bot_generated", "rapid_requests"],
                "indicators": {"bot_score": 95, "repetition_score": 30},
                "recommendation": "Block this request",
            },
        }
        result = _parse_scan_response(data, "req_123")

        assert result.abuse_warnings is not None
        assert result.abuse_warnings.detected is True
        assert result.abuse_warnings.confidence == 90
        assert result.abuse_warnings.abuse_types == ["bot_generated", "rapid_requests"]
        assert result.abuse_warnings.indicators["bot_score"] == 95
        assert result.abuse_warnings.recommendation == "Block this request"

    def test_parse_response_with_routing_info(self):
        """Test parsing response with routing information."""
        data = {
            "safe": True,
            "label": 0,
            "confidence": 95.0,
            "injection": 2.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 50},
            "routing": {
                "enabled": True,
                "task_type": "Code Generation",
                "complexity": 0.85,
                "selected_model": "claude-3-sonnet",
                "reasoning": "High complexity code task",
                "estimated_cost": 0.05,
            },
        }
        result = _parse_scan_response(data, "req_123")

        assert result.routing is not None
        assert result.routing.enabled is True
        assert result.routing.task_type == "Code Generation"
        assert result.routing.complexity == 0.85
        assert result.routing.selected_model == "claude-3-sonnet"
        assert result.routing.reasoning == "High complexity code task"
        assert result.routing.estimated_cost == 0.05

    def test_parse_response_empty_policy_warnings(self):
        """Test parsing response with empty policy_warnings list."""
        data = {
            "safe": True,
            "label": 0,
            "confidence": 95.0,
            "injection": 2.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 25},
            "policy_warnings": [],
        }
        result = _parse_scan_response(data, "req_123")

        assert result.policy_warnings is None

    def test_parse_response_empty_optional_dicts(self):
        """Test parsing response with empty optional dicts."""
        data = {
            "safe": True,
            "label": 0,
            "confidence": 95.0,
            "injection": 2.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 25},
            "scan_warning": {},
            "abuse_warnings": {},
            "routing": {},
        }
        result = _parse_scan_response(data, "req_123")

        assert result.scan_warning is None
        assert result.abuse_warnings is None
        assert result.routing is None

    def test_parse_response_with_policy_confidence(self):
        """Test parsing response with policy_confidence."""
        data = {
            "safe": True,
            "label": 0,
            "confidence": 95.0,
            "injection": 2.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 25},
            "policy_confidence": 88.5,
        }
        result = _parse_scan_response(data, "req_123")

        assert result.policy_confidence == 88.5

    def test_parse_response_fallback_request_id(self):
        """Test fallback request_id when not in response data."""
        data = {
            "safe": True,
            "label": 0,
            "confidence": 95.0,
            "injection": 2.0,
            "sensitivity": "medium",
            "usage": {"requests": 1, "input_chars": 25},
        }
        result = _parse_scan_response(data, "fallback_req_id")

        assert result.request_id == "fallback_req_id"
