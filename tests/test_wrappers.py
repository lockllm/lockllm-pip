"""Tests for provider wrappers."""

import sys
from unittest.mock import Mock, patch

import pytest

from lockllm.errors import ConfigurationError


class TestOpenAIWrapper:
    """Tests for OpenAI wrappers."""

    def test_create_openai(self, api_key):
        """Test creating OpenAI client."""
        # Create mock openai module
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        # Patch sys.modules to inject mock
        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.openai_wrapper import create_openai

            client = create_openai(api_key=api_key)

            assert client == mock_client
            mock_openai.OpenAI.assert_called_once_with(
                api_key=api_key, base_url="https://api.lockllm.com/v1/proxy/openai"
            )

    def test_create_openai_with_custom_base_url(self, api_key):
        """Test creating OpenAI client with custom base URL."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.openai_wrapper import create_openai

            custom_url = "https://custom.lockllm.com/proxy/openai"
            client = create_openai(api_key=api_key, base_url=custom_url)

            mock_openai.OpenAI.assert_called_once_with(
                api_key=api_key, base_url=custom_url
            )

    def test_create_openai_with_extra_kwargs(self, api_key):
        """Test creating OpenAI client with extra kwargs."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.openai_wrapper import create_openai

            client = create_openai(
                api_key=api_key, timeout=30.0, max_retries=5
            )

            call_kwargs = mock_openai.OpenAI.call_args[1]
            assert call_kwargs["timeout"] == 30.0
            assert call_kwargs["max_retries"] == 5

    def test_create_openai_without_openai_installed(self, api_key):
        """Test error when OpenAI is not installed."""
        # Remove openai from sys.modules and mock import to raise ImportError
        modules_copy = sys.modules.copy()
        if 'openai' in sys.modules:
            del sys.modules['openai']

        # Also remove cached imports
        if 'lockllm.wrappers.openai_wrapper' in sys.modules:
            del sys.modules['lockllm.wrappers.openai_wrapper']

        try:
            # Mock __import__ to raise ImportError for openai
            import builtins
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == 'openai':
                    raise ImportError("No module named 'openai'")
                return original_import(name, *args, **kwargs)

            with patch('builtins.__import__', side_effect=mock_import):
                from lockllm.wrappers.openai_wrapper import create_openai

                with pytest.raises(ConfigurationError) as exc_info:
                    create_openai(api_key=api_key)

                assert "OpenAI SDK not found" in str(exc_info.value)
        finally:
            # Restore sys.modules
            sys.modules.update(modules_copy)

    def test_create_async_openai(self, api_key):
        """Test creating async OpenAI client."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.openai_wrapper import create_async_openai

            client = create_async_openai(api_key=api_key)

            assert client == mock_client
            mock_openai.AsyncOpenAI.assert_called_once_with(
                api_key=api_key, base_url="https://api.lockllm.com/v1/proxy/openai"
            )


class TestAnthropicWrapper:
    """Tests for Anthropic wrappers."""

    def test_create_anthropic(self, api_key):
        """Test creating Anthropic client."""
        mock_anthropic = Mock()
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict('sys.modules', {'anthropic': mock_anthropic}):
            from lockllm.wrappers.anthropic_wrapper import create_anthropic

            client = create_anthropic(api_key=api_key)

            assert client == mock_client
            mock_anthropic.Anthropic.assert_called_once_with(
                api_key=api_key, base_url="https://api.lockllm.com/v1/proxy/anthropic"
            )

    def test_create_anthropic_with_custom_base_url(self, api_key):
        """Test creating Anthropic client with custom base URL."""
        mock_anthropic = Mock()
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict('sys.modules', {'anthropic': mock_anthropic}):
            from lockllm.wrappers.anthropic_wrapper import create_anthropic

            custom_url = "https://custom.lockllm.com/proxy/anthropic"
            client = create_anthropic(api_key=api_key, base_url=custom_url)

            mock_anthropic.Anthropic.assert_called_once_with(
                api_key=api_key, base_url=custom_url
            )

    def test_create_async_anthropic(self, api_key):
        """Test creating async Anthropic client."""
        mock_anthropic = Mock()
        mock_client = Mock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        with patch.dict('sys.modules', {'anthropic': mock_anthropic}):
            from lockllm.wrappers.anthropic_wrapper import create_async_anthropic

            client = create_async_anthropic(api_key=api_key)

            assert client == mock_client
            mock_anthropic.AsyncAnthropic.assert_called_once()


class TestGenericWrappers:
    """Tests for generic provider wrappers."""

    def test_create_groq(self, api_key):
        """Test creating Groq client."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import create_groq

            client = create_groq(api_key=api_key)

            assert client == mock_client
            mock_openai.OpenAI.assert_called_once_with(
                api_key=api_key, base_url="https://api.lockllm.com/v1/proxy/groq"
            )

    def test_create_deepseek(self, api_key):
        """Test creating DeepSeek client."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import create_deepseek

            client = create_deepseek(api_key=api_key)

            assert client == mock_client
            call_args = mock_openai.OpenAI.call_args[1]
            assert "deepseek" in call_args["base_url"]

    def test_create_mistral(self, api_key):
        """Test creating Mistral client."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import create_mistral

            client = create_mistral(api_key=api_key)

            assert client == mock_client
            call_args = mock_openai.OpenAI.call_args[1]
            assert "mistral" in call_args["base_url"]

    def test_generic_wrapper_with_custom_base_url(self, api_key):
        """Test generic wrapper with custom base URL."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import create_groq

            custom_url = "https://custom.lockllm.com/proxy/groq"
            client = create_groq(api_key=api_key, base_url=custom_url)

            mock_openai.OpenAI.assert_called_once_with(
                api_key=api_key, base_url=custom_url
            )

    def test_generic_wrapper_with_extra_kwargs(self, api_key):
        """Test generic wrapper with extra kwargs."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import create_groq

            client = create_groq(api_key=api_key, timeout=30.0, max_retries=5)

            call_kwargs = mock_openai.OpenAI.call_args[1]
            assert call_kwargs["timeout"] == 30.0
            assert call_kwargs["max_retries"] == 5

    def test_all_generic_wrappers(self, api_key):
        """Test all generic wrapper functions."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.OpenAI.return_value = mock_client
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import (
                create_perplexity,
                create_async_perplexity,
                create_openrouter,
                create_async_openrouter,
                create_together,
                create_async_together,
                create_xai,
                create_async_xai,
                create_fireworks,
                create_async_fireworks,
                create_anyscale,
                create_async_anyscale,
                create_huggingface,
                create_async_huggingface,
                create_gemini,
                create_async_gemini,
                create_cohere,
                create_async_cohere,
                create_azure,
                create_async_azure,
                create_bedrock,
                create_async_bedrock,
                create_vertex_ai,
                create_async_vertex_ai,
            )

            # Test sync wrappers
            create_perplexity(api_key=api_key)
            create_openrouter(api_key=api_key)
            create_together(api_key=api_key)
            create_xai(api_key=api_key)
            create_fireworks(api_key=api_key)
            create_anyscale(api_key=api_key)
            create_huggingface(api_key=api_key)
            create_gemini(api_key=api_key)
            create_cohere(api_key=api_key)
            create_azure(api_key=api_key)
            create_bedrock(api_key=api_key)
            create_vertex_ai(api_key=api_key)

            # Test async wrappers
            create_async_perplexity(api_key=api_key)
            create_async_openrouter(api_key=api_key)
            create_async_together(api_key=api_key)
            create_async_xai(api_key=api_key)
            create_async_fireworks(api_key=api_key)
            create_async_anyscale(api_key=api_key)
            create_async_huggingface(api_key=api_key)
            create_async_gemini(api_key=api_key)
            create_async_cohere(api_key=api_key)
            create_async_azure(api_key=api_key)
            create_async_bedrock(api_key=api_key)
            create_async_vertex_ai(api_key=api_key)

            # Verify they all used the mock
            assert mock_openai.OpenAI.call_count >= 12
            assert mock_openai.AsyncOpenAI.call_count >= 12

    def test_async_groq_deepseek_mistral(self, api_key):
        """Test async versions of groq, deepseek, and mistral."""
        mock_openai = Mock()
        mock_client = Mock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict('sys.modules', {'openai': mock_openai}):
            from lockllm.wrappers.generic_wrapper import (
                create_async_groq,
                create_async_deepseek,
                create_async_mistral,
            )

            # Test the three specific async functions that were missing coverage
            client1 = create_async_groq(api_key=api_key)
            client2 = create_async_deepseek(api_key=api_key)
            client3 = create_async_mistral(api_key=api_key)

            assert client1 == mock_client
            assert client2 == mock_client
            assert client3 == mock_client

            # Verify AsyncOpenAI was called 3 times
            assert mock_openai.AsyncOpenAI.call_count == 3


class TestWrapperImports:
    """Test that all wrapper functions are importable."""

    def test_all_wrappers_importable(self):
        """Test that all wrapper functions can be imported."""
        from lockllm.wrappers import (
            create_anyscale,
            create_anthropic,
            create_async_anyscale,
            create_async_anthropic,
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

        # Just verify they're all callable
        assert callable(create_openai)
        assert callable(create_async_openai)
        assert callable(create_anthropic)
        assert callable(create_async_anthropic)
        assert callable(create_groq)
        assert callable(create_async_groq)


class TestWrapperErrorHandling:
    """Test wrapper error handling."""

    def test_anthropic_wrapper_import_error(self, api_key):
        """Test ConfigurationError when anthropic SDK not installed."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'anthropic':
                raise ImportError("No module named 'anthropic'")
            return original_import(name, *args, **kwargs)

        # Remove from cache
        modules_copy = sys.modules.copy()
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        if 'lockllm.wrappers.anthropic_wrapper' in sys.modules:
            del sys.modules['lockllm.wrappers.anthropic_wrapper']

        try:
            with patch('builtins.__import__', side_effect=mock_import):
                from lockllm.wrappers.anthropic_wrapper import create_anthropic

                with pytest.raises(ConfigurationError) as exc_info:
                    create_anthropic(api_key=api_key)

                assert "Anthropic SDK not found" in str(exc_info.value)
        finally:
            sys.modules.update(modules_copy)

    def test_async_anthropic_wrapper_import_error(self, api_key):
        """Test ConfigurationError when anthropic SDK not installed for async."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'anthropic':
                raise ImportError("No module named 'anthropic'")
            return original_import(name, *args, **kwargs)

        modules_copy = sys.modules.copy()
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']
        if 'lockllm.wrappers.anthropic_wrapper' in sys.modules:
            del sys.modules['lockllm.wrappers.anthropic_wrapper']

        try:
            with patch('builtins.__import__', side_effect=mock_import):
                from lockllm.wrappers.anthropic_wrapper import create_async_anthropic

                with pytest.raises(ConfigurationError) as exc_info:
                    create_async_anthropic(api_key=api_key)

                assert "Anthropic SDK not found" in str(exc_info.value)
        finally:
            sys.modules.update(modules_copy)

    def test_generic_wrapper_import_error(self, api_key):
        """Test ConfigurationError when openai SDK not installed for generic wrappers."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'openai':
                raise ImportError("No module named 'openai'")
            return original_import(name, *args, **kwargs)

        modules_copy = sys.modules.copy()
        if 'openai' in sys.modules:
            del sys.modules['openai']
        if 'lockllm.wrappers.generic_wrapper' in sys.modules:
            del sys.modules['lockllm.wrappers.generic_wrapper']

        try:
            with patch('builtins.__import__', side_effect=mock_import):
                from lockllm.wrappers.generic_wrapper import create_groq

                with pytest.raises(ConfigurationError) as exc_info:
                    create_groq(api_key=api_key)

                assert "OpenAI SDK not found" in str(exc_info.value) or "openai" in str(exc_info.value).lower()
        finally:
            sys.modules.update(modules_copy)

    def test_async_openai_wrapper_import_error(self, api_key):
        """Test ConfigurationError for async openai when SDK not installed."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'openai':
                raise ImportError("No module named 'openai'")
            return original_import(name, *args, **kwargs)

        modules_copy = sys.modules.copy()
        if 'openai' in sys.modules:
            del sys.modules['openai']
        if 'lockllm.wrappers.openai_wrapper' in sys.modules:
            del sys.modules['lockllm.wrappers.openai_wrapper']

        try:
            with patch('builtins.__import__', side_effect=mock_import):
                from lockllm.wrappers.openai_wrapper import create_async_openai

                with pytest.raises(ConfigurationError) as exc_info:
                    create_async_openai(api_key=api_key)

                assert "OpenAI SDK not found" in str(exc_info.value)
        finally:
            sys.modules.update(modules_copy)
