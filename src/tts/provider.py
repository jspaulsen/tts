from typing import Protocol, TypeVar

VoiceT = TypeVar("VoiceT", bound=str, contravariant=True)


class TTSProvider(Protocol[VoiceT]):
    async def synthesize_speech(
        self,
        voice: VoiceT,
        text: str,
        **kwargs,
    ) -> bytes:
        ...
