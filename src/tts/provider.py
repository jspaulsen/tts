from typing import Protocol, TypeVar


V = TypeVar('V', bound=str, contravariant=True)


class TTSProvider(Protocol[V]):
    async def synthesize_speech(
        self,
        voice: V,
        text: str,
        **kwargs,
    ) -> bytes:
        ...

    def generate_cache(
        self,
        voice: str,
        text: str,
        **kwargs,
    ) -> str:
        nvoice: str = voice.lower()
        ntext: str = text.strip().lower()

        return f"{nvoice}:{ntext}"


    @staticmethod
    def voices() -> list[str]:
        ...

    @property
    def can_cache(self) -> bool:
        """
        Indicates whether the provider supports caching of synthesized speech.

        Generally, neural voices are stochastic and should not be cached, while standard voices can be cached.
        """
        ...

    @property
    def supports_ssml(self) -> bool:
        """
        Indicates whether the provider supports SSML input.
        """
        ...

    @property
    def has_financial_cost(self) -> bool:
        """
        Indicates whether the provider incurs a cost for usage.
        """
        ...
