"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "llm_test_key_123456"


@pytest.fixture
def mock_scan_response():
    """Return a mock scan response."""
    return {
        "safe": True,
        "label": 0,
        "confidence": 95,
        "injection": 2,
        "sensitivity": "medium",
        "request_id": "test_request_123",
        "usage": {
            "requests": 1,
            "input_chars": 25,
        },
    }


@pytest.fixture
def mock_unsafe_scan_response():
    """Return a mock unsafe scan response."""
    return {
        "safe": False,
        "label": 1,
        "confidence": 92,
        "injection": 87,
        "sensitivity": "medium",
        "request_id": "test_request_456",
        "usage": {
            "requests": 1,
            "input_chars": 50,
        },
        "debug": {
            "duration_ms": 150,
            "inference_ms": 120,
            "mode": "single",
        },
    }


@pytest.fixture
def mock_error_response():
    """Return a mock error response."""
    return {
        "error": {
            "message": "Invalid API key",
            "type": "authentication_error",
            "code": "unauthorized",
        }
    }


@pytest.fixture
def mock_injection_error_response():
    """Return a mock prompt injection error response."""
    return {
        "error": {
            "message": "Prompt injection detected",
            "type": "lockllm_security_error",
            "code": "prompt_injection_detected",
            "request_id": "test_request_789",
            "scan_result": {
                "safe": False,
                "label": 1,
                "confidence": 95,
                "injection": 90,
                "sensitivity": "high",
            },
        }
    }
