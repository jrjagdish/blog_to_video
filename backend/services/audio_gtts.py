import os
from gtts import gTTS

def generate_audio(text: str, output_path: str = "output.mp3", lang: str = "en"):
    """
    Generates an MP3 file from text using gTTS.
    """
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_path)
    return output_path
