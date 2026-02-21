"""Tests for main package initialization."""

import lockllm


class TestPackageInit:
    """Tests for package-level imports and metadata."""

    def test_version(self):
        """Test that version is defined."""
        assert hasattr(lockllm, "__version__")
        assert lockllm.__version__ == "1.2.0"

    def test_main_clients_importable(self):
        """Test that main clients are importable."""
        assert hasattr(lockllm, "LockLLM")
        assert hasattr(lockllm, "AsyncLockLLM")

    def test_errors_importable(self):
        """Test that error classes are importable."""
        assert hasattr(lockllm, "LockLLMError")
        assert hasattr(lockllm, "AuthenticationError")
        assert hasattr(lockllm, "RateLimitError")
        assert hasattr(lockllm, "PromptInjectionError")
        assert hasattr(lockllm, "UpstreamError")
        assert hasattr(lockllm, "ConfigurationError")
        assert hasattr(lockllm, "NetworkError")

    def test_types_importable(self):
        """Test that type definitions are importable."""
        assert hasattr(lockllm, "LockLLMConfig")
        assert hasattr(lockllm, "ScanRequest")
        assert hasattr(lockllm, "ScanResponse")
        assert hasattr(lockllm, "ScanResult")

    def test_utils_importable(self):
        """Test that utility functions are importable."""
        assert hasattr(lockllm, "get_proxy_url")
        assert hasattr(lockllm, "get_all_proxy_urls")

    def test_wrappers_importable(self):
        """Test that wrapper functions are importable."""
        assert hasattr(lockllm, "create_openai")
        assert hasattr(lockllm, "create_async_openai")
        assert hasattr(lockllm, "create_anthropic")
        assert hasattr(lockllm, "create_async_anthropic")
        assert hasattr(lockllm, "create_groq")
        assert hasattr(lockllm, "create_async_groq")

    def test_all_contains_expected_exports(self):
        """Test that __all__ contains expected exports."""
        assert "__version__" in lockllm.__all__
        assert "LockLLM" in lockllm.__all__
        assert "AsyncLockLLM" in lockllm.__all__
        assert "LockLLMError" in lockllm.__all__
        assert "create_openai" in lockllm.__all__
        assert "create_async_openai" in lockllm.__all__

    def test_all_exports_are_valid(self):
        """Test that all items in __all__ are actually exported."""
        for name in lockllm.__all__:
            assert hasattr(lockllm, name), f"{name} in __all__ but not exported"
