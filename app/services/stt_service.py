import whisper
import os

class STTService:
    def __init__(self, model_name: str = "base"):
        """
        Initializes the Whisper model. You can use 'tiny', 'base', 'small', 'medium', 'large'.
        'base' is a good tradeoff between speed and accuracy for local dev.
        """
        self.model = whisper.load_model(model_name)

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes the given audio file using Whisper.
        Uses a prompt to preserve filler words like 'eee', 'ııı'.
        """
        # initial_prompt is used to guide the model to keep filler words and stuttering
        initial_prompt = "Umm, ııı, şey, hıhı gibi sesleri ve kekelemeleri olduğu gibi yazıya dök. Aynen böyle: eee, ııı, kem, küm, hı hı..."
        
        result = self.model.transcribe(
            audio_path,
            initial_prompt=initial_prompt,
            # We can also force the language if needed: language="tr"
            language="tr"
        )
        
        return result["text"].strip()
