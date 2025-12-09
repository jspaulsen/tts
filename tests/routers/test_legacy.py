from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from fastapi.testclient import TestClient

from src.configuration import Configuration
from src.routers.legacy import cache_key



class TestCacheKey:
    """Tests for the cache_key function."""

    def test_cache_key_basic(self):
        """Test cache key generation with basic inputs."""

        result = cache_key("Amy", "Hello world", "text")
        assert result == "amy:text:hello world"


class TestLegacySpeechEndpoint:
    """Tests for the /legacy/speech endpoint."""

    @pytest.fixture
    def user_token(self, client: TestClient, auth_headers: dict[str, str]) -> str:
        """Create a test user and return their API token."""
        username = f"test-legacy-{uuid.uuid4()}"
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={"username": username},
        )
        assert response.status_code == 200
        return response.json()["api_token"]

    @pytest.fixture
    def auth_headers(self) -> dict[str, str]:
        config = Configuration.get()
        return {"Authorization": f"Bearer {config.admin_api_token}"}

    def test_speech_unauthorized_no_token(self, client: TestClient):
        """Test that /legacy/speech returns 401 when token is empty."""
        response = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "Hello", "token": ""},
        )
        assert response.status_code == 401

    def test_speech_unauthorized_invalid_token(self, client: TestClient):
        """Test that /legacy/speech returns 401 with invalid token."""
        response = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "Hello", "token": "invalid-token"},
        )
        assert response.status_code == 401

    def test_speech_text_too_long(
        self,
        client: TestClient,
        user_token: str,
    ):
        """Test that /legacy/speech returns 413 when text exceeds max length."""
        config = Configuration.get()
        long_text = "a" * (config.maximum_characters_per_request + 1)

        response = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": long_text, "token": user_token},
        )
        assert response.status_code == 413
        assert "exceeds maximum" in response.json()["detail"]

    def test_speech_invalid_ssml(
        self,
        client: TestClient,
        user_token: str,
    ):
        """Test that /legacy/speech returns 400 for invalid SSML."""
        response = client.get(
            "/legacy/speech",
            params={
                "voice": "Amy",
                "text": "<speak>unclosed tag",
                "text_type": "ssml",
                "token": user_token,
            },
        )
        assert response.status_code == 400
        assert "Invalid SSML format" in response.json()["detail"]

    def test_speech_success(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test successful speech synthesis."""
        mock_audio_content = b"fake-audio-content"

        # Create a mock streaming body
        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=mock_audio_content)

        # Create mock polly client
        mock_polly_client = AsyncMock()
        mock_polly_client.synthesize_speech = AsyncMock(
            return_value={"AudioStream": mock_stream}
        )
        mock_polly_client.exceptions = MagicMock()

        # Create async context manager for the client
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        # Mock the PollyProvider.get method
        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        response = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "Hello world", "token": user_token},
        )

        assert response.status_code == 200
        assert response.content == mock_audio_content
        assert response.headers["content-type"] == "audio/mpeg"

        # Verify polly was called with correct parameters
        mock_polly_client.synthesize_speech.assert_called_once_with(
            Text="Hello world",
            OutputFormat="mp3",
            VoiceId="Amy",
            TextType="text",
        )

    def test_speech_with_ssml(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test speech synthesis with valid SSML."""
        mock_audio_content = b"fake-ssml-audio"

        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=mock_audio_content)

        mock_polly_client = AsyncMock()
        mock_polly_client.synthesize_speech = AsyncMock(
            return_value={"AudioStream": mock_stream}
        )
        mock_polly_client.exceptions = MagicMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        ssml_text = "<speak>Hello world</speak>"
        response = client.get(
            "/legacy/speech",
            params={
                "voice": "Brian",
                "text": ssml_text,
                "text_type": "ssml",
                "token": user_token,
            },
        )

        assert response.status_code == 200
        assert response.content == mock_audio_content

        mock_polly_client.synthesize_speech.assert_called_once_with(
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId="Brian",
            TextType="ssml",
        )

    def test_speech_returns_cached_response(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test that cached responses are returned without calling Polly."""
        mock_audio_content = b"cached-audio-content"

        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=mock_audio_content)

        mock_polly_client = AsyncMock()
        mock_polly_client.synthesize_speech = AsyncMock(
            return_value={"AudioStream": mock_stream}
        )
        mock_polly_client.exceptions = MagicMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        # First request - should call Polly
        response1 = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "cache test", "token": user_token},
        )
        assert response1.status_code == 200
        assert mock_polly_client.synthesize_speech.call_count == 1

        # Second request with same parameters - should use cache
        response2 = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "cache test", "token": user_token},
        )
        assert response2.status_code == 200
        assert response2.content == mock_audio_content
        # Polly should not be called again
        assert mock_polly_client.synthesize_speech.call_count == 1

    def test_speech_polly_invalid_ssml_exception(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test handling of Polly InvalidSsmlException."""
        # Create a mock exception class
        class MockInvalidSsmlException(Exception):
            pass

        mock_polly_client = AsyncMock()
        mock_polly_client.exceptions = MagicMock()
        mock_polly_client.exceptions.InvalidSsmlException = MockInvalidSsmlException
        mock_polly_client.synthesize_speech = AsyncMock(
            side_effect=MockInvalidSsmlException("Invalid SSML")
        )

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        # Use valid XML but Polly rejects it
        response = client.get(
            "/legacy/speech",
            params={
                "voice": "Amy",
                "text": "<speak><invalid-tag/></speak>",
                "text_type": "ssml",
                "token": user_token,
            },
        )

        assert response.status_code == 400
        assert "SSML synthesis error" in response.json()["detail"]

    def test_speech_polly_generic_exception(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test handling of generic Polly exceptions."""
        mock_polly_client = AsyncMock()
        mock_polly_client.exceptions = MagicMock()
        mock_polly_client.exceptions.InvalidSsmlException = type(
            "InvalidSsmlException", (Exception,), {}
        )
        mock_polly_client.synthesize_speech = AsyncMock(
            side_effect=RuntimeError("AWS connection error")
        )

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        response = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "test", "token": user_token},
        )

        assert response.status_code == 500
        assert "error occurred during speech synthesis" in response.json()["detail"]

    def test_speech_cache_key_case_insensitive(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test that cache key is case insensitive for text."""
        mock_audio_content = b"audio-content"

        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=mock_audio_content)

        mock_polly_client = AsyncMock()
        mock_polly_client.synthesize_speech = AsyncMock(
            return_value={"AudioStream": mock_stream}
        )
        mock_polly_client.exceptions = MagicMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        # First request with lowercase
        response1 = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "hello", "token": user_token},
        )
        assert response1.status_code == 200
        assert mock_polly_client.synthesize_speech.call_count == 1

        # Second request with uppercase - should hit cache
        response2 = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": "HELLO", "token": user_token},
        )
        assert response2.status_code == 200
        # Cache hit, so Polly shouldn't be called again
        assert mock_polly_client.synthesize_speech.call_count == 1

    def test_speech_different_voices_not_cached_together(
        self,
        client: TestClient,
        user_token: str,
        mocker,
    ):
        """Test that different voices have different cache keys."""
        import uuid

        mock_audio_content = b"audio-content"

        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=mock_audio_content)

        mock_polly_client = AsyncMock()
        mock_polly_client.synthesize_speech = AsyncMock(
            return_value={"AudioStream": mock_stream}
        )
        mock_polly_client.exceptions = MagicMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_polly_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mocker.patch(
            "src.routers.legacy.PollyProvider.get",
            return_value=mock_context,
        )

        # Use unique text to avoid cache collisions with other tests
        unique_text = f"voice-test-{uuid.uuid4()}"

        # Request with Amy
        response1 = client.get(
            "/legacy/speech",
            params={"voice": "Amy", "text": unique_text, "token": user_token},
        )
        assert response1.status_code == 200

        # Request with Brian - same text but different voice
        response2 = client.get(
            "/legacy/speech",
            params={"voice": "Brian", "text": unique_text, "token": user_token},
        )
        assert response2.status_code == 200
        # Should call Polly twice since different voices
        assert mock_polly_client.synthesize_speech.call_count == 2
