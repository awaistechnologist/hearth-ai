import logging
import os
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initialize Faster Whisper.
        On RPi, we strictly use CPU and int8 quantization for speed/ram balance.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def load_model(self):
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_size}...")
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("Whisper model loaded.")

    def unload_model(self):
        """
        Explicitly delete the model to free up RAM.
        """
        if self.model:
            del self.model
            self.model = None
            import gc
            gc.collect()
            logger.info("Whisper model unloaded.")

    def transcribe(self, file_path: str) -> str:
        """
        Transcribe audio file to text.
        """
        self.load_model()
        
        try:
            segments, info = self.model.transcribe(file_path, beam_size=5)
            logger.info(f"Detected language '{info.language}' with probability {info.language_probability}")
            
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        finally:
            # Aggressive memory management for RPi
            # We unload after every use to ensure LLM has max RAM
            self.unload_model()
