from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from fastapi.testclient import TestClient

from src.configuration import Configuration


class TestSpeechEndpoint:
    @pytest.fixture
    def user_token(self, client: TestClient, auth_headers: dict[str, str]) -> str:
        """Create a test user and return their API token."""
        username = f"test-speech-{uuid.uuid4()}"
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
        return {"Authorization": f"Bearer {config.admin_api_token.get_secret_value()}"}

    @pytest.fixture
    def user_auth_headers(self, user_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {user_token}"}

    def test_speech_unauthorized_no_token(self, client: TestClient):
        """Test that /v1/speech returns 401 when no authorization header is provided."""
        response = client.post(
            "/v1/speech",
            json={"voice": "Amy", "text": "Hello"},
        )
        assert response.status_code == 401

    def test_speech_unauthorized_invalid_token(self, client: TestClient):
        """Test that /v1/speech returns 401 with invalid token."""
        response = client.post(
            "/v1/speech",
            headers={"Authorization": "Bearer invalid-token"},
            json={"voice": "Amy", "text": "Hello"},
        )
        assert response.status_code == 401

    def test_speech_invalid_ssml(
        self,
        client: TestClient,
        user_auth_headers: dict[str, str],
    ):
        """Test that /v1/speech returns 400 for invalid SSML."""
        response = client.post(
            "/v1/speech",
            headers=user_auth_headers,
            json={
                "voice": "Amy",
                "text": "<speak>unclosed tag",
                "text_type": "ssml",
            },
        )
        assert response.status_code == 400
        assert "Invalid SSML format" in response.json()["detail"]

    def test_speech_success_polly_voice(
        self,
        client: TestClient,
        user_auth_headers: dict[str, str],
        mocker,
    ):
        """Test successful speech synthesis with Polly voice."""
        mock_audio_content = b"fake-audio-content"

        mock_synthesize = mocker.patch(
            "src.routers.speech.PollyProvider.synthesize_speech",
            new_callable=AsyncMock,
            return_value=mock_audio_content,
        )

        response = client.post(
            "/v1/speech",
            headers=user_auth_headers,
            json={"voice": "Amy", "text": "Hello world"},
        )

        assert response.status_code == 200
        assert response.content == mock_audio_content
        assert response.headers["content-type"] == "audio/mpeg"

        mock_synthesize.assert_called_once_with("Amy", "Hello world")

    def test_speech_success_kokoro_voice(
        self,
        client: TestClient,
        user_auth_headers: dict[str, str],
        mocker,
    ):
        """Test successful speech synthesis with Kokoro voice."""
        mock_audio_content = b"fake-kokoro-audio"

        mock_synthesize = mocker.patch(
            "src.tts.kokoro.KokoroProvider.synthesize_speech",
            new_callable=AsyncMock,
            return_value=mock_audio_content,
        )

        response = client.post(
            "/v1/speech",
            headers=user_auth_headers,
            json={"voice": "af_heart", "text": "Hello from Kokoro"},
        )

        assert response.status_code == 200
        assert response.content == mock_audio_content
        assert response.headers["content-type"] == "audio/mpeg"

        mock_synthesize.assert_called_once_with("af_heart", "Hello from Kokoro")

    def test_speech_returns_cached_response(
        self,
        client: TestClient,
        user_auth_headers: dict[str, str],
        mocker,
    ):
        """Test that cached responses are returned without calling provider."""
        mock_audio_content = b"cached-audio-content"

        mock_synthesize = mocker.patch(
            "src.routers.speech.PollyProvider.synthesize_speech",
            new_callable=AsyncMock,
            return_value=mock_audio_content,
        )

        unique_text = f"cache test {uuid.uuid4()}"

        # First request - should call provider
        response1 = client.post(
            "/v1/speech",
            headers=user_auth_headers,
            json={"voice": "Amy", "text": unique_text},
        )
        assert response1.status_code == 200
        assert mock_synthesize.call_count == 1

        # Second request with same parameters - should use cache
        response2 = client.post(
            "/v1/speech",
            headers=user_auth_headers,
            json={"voice": "Amy", "text": unique_text},
        )
        assert response2.status_code == 200
        assert response2.content == mock_audio_content
        # Provider should not be called again
        assert mock_synthesize.call_count == 1

    def test_speech_content_disposition_header(
        self,
        client: TestClient,
        user_auth_headers: dict[str, str],
        mocker,
    ):
        """Test that response includes correct Content-Disposition header."""
        mock_audio_content = b"audio-content"

        mocker.patch(
            "src.routers.speech.PollyProvider.synthesize_speech",
            new_callable=AsyncMock,
            return_value=mock_audio_content,
        )

        response = client.post(
            "/v1/speech",
            headers=user_auth_headers,
            json={"voice": "Amy", "text": "test"},
        )

        assert response.status_code == 200
        assert 'filename="Amy.mp3"' in response.headers["content-disposition"]
