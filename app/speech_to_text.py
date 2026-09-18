"""
speech_to_text.py - Microphone capture + Google Web Speech STT.

Supports both sounddevice (pre-built wheels, no C++ build tools needed)
and standard PyAudio / SpeechRecognition Microphone.
"""

import time
import math
from app.utils import get_logger

logger = get_logger(__name__)

# Check SpeechRecognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    logger.warning("SpeechRecognition is not installed.")

# Check sounddevice + numpy
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    logger.warning("sounddevice or numpy not installed.")

# Check PyAudio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class SpeechToText:
    """Wraps audio capture and speech-to-text recognition."""

    def __init__(self):
        self._recognizer = sr.Recognizer() if SR_AVAILABLE else None
        self._mic_index: int | None = None
        self._sample_rate = 16000

    @property
    def is_available(self) -> bool:
        """Returns True if STT engine and at least one audio input backend is present."""
        return SR_AVAILABLE and (SOUNDDEVICE_AVAILABLE or PYAUDIO_AVAILABLE)

    def set_microphone_index(self, index: int):
        """Set microphone device index (-1 or negative = default)."""
        self._mic_index = index if index >= 0 else None

    def list_microphones(self) -> list[str]:
        """List human-friendly input microphone names."""
        if SOUNDDEVICE_AVAILABLE:
            try:
                devices = sd.query_devices()
                mics = []
                for i, dev in enumerate(devices):
                    if dev.get("max_input_channels", 0) > 0:
                        mics.append(f"[{i}] {dev['name']}")
                return mics
            except Exception as e:
                logger.warning("Failed to query sounddevice input devices: %s", e)

        if PYAUDIO_AVAILABLE and SR_AVAILABLE:
            try:
                return sr.Microphone.list_microphone_names()
            except Exception as e:
                logger.warning("Failed to query sr.Microphone names: %s", e)

        return []

    def listen(self, timeout: int = 8, phrase_limit: int = 15) -> str:
        """
        Record audio from the selected microphone and run STT.

        Raises:
            RuntimeError: If audio hardware or dependencies are missing.
            ValueError: If no speech or unrecognized speech.
        """
        if not SR_AVAILABLE:
            raise RuntimeError(
                "SpeechRecognition library is not installed. Run: pip install SpeechRecognition"
            )

        if not (SOUNDDEVICE_AVAILABLE or PYAUDIO_AVAILABLE):
            raise RuntimeError(
                "No audio recording backend available. Install sounddevice: pip install sounddevice numpy"
            )

        audio_data = None

        if SOUNDDEVICE_AVAILABLE:
            audio_data = self._record_sounddevice(timeout=timeout, phrase_limit=phrase_limit)
        else:
            audio_data = self._record_pyaudio(timeout=timeout, phrase_limit=phrase_limit)

        if audio_data is None:
            raise ValueError("No speech detected within the timeout period.")

        try:
            text = self._recognizer.recognize_google(audio_data)
            logger.info("STT recognized: %r", text)
            return text.strip()
        except sr.UnknownValueError:
            raise ValueError("I couldn't understand that. Please try again.")
        except sr.RequestError as e:
            logger.error("STT network error: %s", e)
            raise ValueError(
                "Speech recognition service is unavailable. Please check your internet connection."
            ) from e

    def _record_sounddevice(self, timeout: int = 8, phrase_limit: int = 15) -> sr.AudioData:
        """Record from microphone using sounddevice with adaptive energy & silence detection."""
        sample_rate = self._sample_rate
        chunk_duration = 0.1  # 100 ms chunks
        chunk_samples = int(sample_rate * chunk_duration)
        device = self._mic_index

        logger.debug("Opening sounddevice InputStream (device=%s, rate=%s)", device, sample_rate)

        try:
            stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
                device=device,
            )
        except Exception as e:
            logger.error("Failed to open microphone stream: %s", e)
            raise RuntimeError(f"Could not open microphone device: {e}") from e

        with stream:
            # 1. Ambient noise calibration (0.4s)
            calib_chunks = []
            for _ in range(4):
                data, _ = stream.read(chunk_samples)
                calib_chunks.append(np.abs(data).mean())
            ambient = max(15.0, float(np.mean(calib_chunks)))
            speech_threshold = ambient * 2.2 + 20.0
            logger.debug("Ambient noise: %.2f | Speech threshold: %.2f", ambient, speech_threshold)

            # 2. Listen loop
            recorded_chunks = []
            speech_started = False
            start_wait_time = time.time()
            speech_start_time = None
            silence_start_time = None
            pause_threshold = 0.8  # seconds of silence to terminate

            while True:
                data, _ = stream.read(chunk_samples)
                energy = float(np.abs(data).mean())
                now = time.time()

                if not speech_started:
                    # Waiting for user to begin speaking
                    if energy > speech_threshold:
                        speech_started = True
                        speech_start_time = now
                        recorded_chunks.append(data)
                        logger.debug("Speech detected!")
                    elif now - start_wait_time > timeout:
                        raise ValueError("No speech detected within the timeout period.")
                else:
                    # User is currently speaking
                    recorded_chunks.append(data)

                    # Check max phrase limit
                    if now - speech_start_time > phrase_limit:
                        logger.debug("Phrase limit reached.")
                        break

                    # Check trailing silence
                    if energy < speech_threshold:
                        if silence_start_time is None:
                            silence_start_time = now
                        elif now - silence_start_time >= pause_threshold:
                            logger.debug("Silence detected after speech, finishing.")
                            break
                    else:
                        silence_start_time = None

            if not recorded_chunks:
                raise ValueError("No speech detected within the timeout period.")

            full_audio = np.concatenate(recorded_chunks, axis=0)
            raw_bytes = full_audio.tobytes()
            return sr.AudioData(raw_bytes, sample_rate, 2)

    def _record_pyaudio(self, timeout: int = 8, phrase_limit: int = 15) -> sr.AudioData:
        """Fallback to speech_recognition Microphone if sounddevice is absent."""
        try:
            with sr.Microphone(device_index=self._mic_index) as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
                return self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except OSError as e:
            logger.error("PyAudio microphone error: %s", e)
            raise RuntimeError(
                "Microphone not found or not accessible. Please check your microphone connection."
            ) from e
        except sr.WaitTimeoutError:
            raise ValueError("No speech detected within the timeout period.")