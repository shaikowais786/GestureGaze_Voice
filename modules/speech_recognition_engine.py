import os
import sys
import logging
import pyaudio
import numpy as np
import speech_recognition as sr
import time

class SpeechRecognitionEngine:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()
        
        # 🧠 FIX 3: OPTIMIZE RECOGNIZER (VERY IMPORTANT)
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 1.2 # Allows natural pauses in speech
        
        self.microphone = None
        self._initialize_microphone()

    def _initialize_microphone(self):
        try:
            # Use system default microphone instead of hardcoded index
            self.microphone = sr.Microphone(device_index=None, sample_rate=self.sample_rate)
            
            # Log the mic name for demo purposes
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                default_idx = p.get_default_input_device_info()['index']
                mics = sr.Microphone.list_microphone_names()
                mic_name = mics[default_idx] if default_idx < len(mics) else "System Default"
                logging.info(f"Using microphone: [{default_idx}] {mic_name}")
                p.terminate()
            except Exception:
                logging.info("Using system default microphone")

            with self.microphone as source:
                logging.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            logging.info("Microphone initialized successfully.")
        except OSError as e:
            logging.warning(f"No input audio device available: {e}")
            self.microphone = None
        except Exception as e:
            logging.critical(f"Failed to initialize microphone: {e}")
            self.microphone = None


    def stop(self):
        """Placeholder to prevent AttributeErrors on application exit shutdown calls."""
        pass
        
    def get_audio_sample(self, duration=3):
        """
        Captures a raw audio sample for speaker authentication.
        """
        logging.info(f"Recording {duration}s sample...")
        
        # Create a fresh microphone instance because the main one is locked by the background listening thread
        device_index = None
        if self.microphone:
            device_index = self.microphone.device_index
            
        temp_mic = sr.Microphone(device_index=device_index, sample_rate=self.sample_rate)
        
        # We manually record for the exact duration needed for registration
        with temp_mic as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5) # Quick calibration
                # Listen specifically for the duration required
                audio_data = self.recognizer.record(source, duration=duration)
                
                logging.info("Recording complete.")
                
                # Convert to numpy array
                raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
                audio_int16 = np.frombuffer(raw_data, dtype=np.int16)
                audio_float = audio_int16.astype(np.float32) / 32768.0
                
                return audio_float
            except Exception as e:
                logging.error(f"Failed to record sample: {e}")
                return None
