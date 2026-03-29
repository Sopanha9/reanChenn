import os
from gtts import gTTS

def speak_chinese(text: str) -> str:
    """
    Converts Chinese text to an MP3 audio file using Google Text-to-Speech (gTTS).
    
    Args:
        text (str): The Chinese text to speak.
        
    Returns:
        str: The file path to the generated audio file (temp_audio.mp3).
    """
    file_path = "temp_audio.mp3"
    
    try:
        tts = gTTS(text=text, lang='zh')
        tts.save(file_path)
        return file_path
    except Exception as e:
        print(f"Error generating TTS: {str(e)}")
        return None
