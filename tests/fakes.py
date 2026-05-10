"""Fake implementations of external services for testing."""

from dataclasses import dataclass


@dataclass
class FakeSynthesizeResponse:
    """Mimics the response from TextToSpeechClient.synthesize_speech."""

    audio_content: bytes


class FakeTextToSpeechClient:
    """Fake Google Cloud TTS client that returns dummy audio bytes.

    Records all calls for assertion in tests.
    """

    def __init__(self, audio_bytes: bytes = b"fake-mp3-audio-content"):
        self.audio_bytes = audio_bytes
        self.calls: list[dict] = []

    def synthesize_speech(self, *, input, voice, audio_config):
        self.calls.append(
            {
                "input": input,
                "voice": voice,
                "audio_config": audio_config,
            }
        )
        return FakeSynthesizeResponse(audio_content=self.audio_bytes)
