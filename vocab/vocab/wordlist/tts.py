from dataclasses import dataclass
from typing import Any

from elevenlabs.client import ElevenLabs

VOICES = {
    "leonie": "uvysWDLbKpA4XvpD3GI6",
    "otto": "FTNCalFNG5bRnkkaP5Ug",
    "helmut": "dFA3XRddYScy6ylAYTIO",
    "lea": "7eVMgwCnXydb3CikjV7a",
}
MODELS = {
    "high_quality": "eleven_multilingual_v2",
    "low_latency": "eleven_flash_v2_5",
}
OUTPUT_FORMATS = {
    "mp3_32k": "mp3_22050_32",
    "mp3_48k": "mp3_24000_48",
    "mp3_128k": "mp3_44100_128",
}


@dataclass
class TTSApi:
    api_key: str = None
    client: Any | None = None

    def __post_init__(self):
        self.client = ElevenLabs(api_key=self.api_key)

    def generate_audio(
        self,
        text: str,
        model: str = "high_quality",
        voice: str = "lea",
        output_format: str = "mp3_48k",
    ) -> bytes:
        voice_id = VOICES.get(voice)
        model_id = MODELS.get(model)
        output_format = OUTPUT_FORMATS.get(output_format)
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
        )
        return audio

    def generate_file(self, audio: bytes, filename: str) -> None:
        with open(filename, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
