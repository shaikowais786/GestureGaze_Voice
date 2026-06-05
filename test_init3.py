import logging
import sys
import time
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
from modules.speech_recognition_engine import SpeechRecognitionEngine

logging.info("Initializing engine...")
engine = SpeechRecognitionEngine()

def dummy_callback(text, audio_float):
    logging.info(f"CALLED BACK with text: {text}")

logging.info("Starting listen_continuously...")
# I'll modify listen_continuously locally or just run it to see if it responds to my PC mic? No wait, this is running on the USER's PC.
# Since I'm running this on the USER's actual PC, if I make it listen and it doesn't print anything, it means the mic isn't picking up or the user isn't speaking right now.
# Or I can just check if listen_in_background callback ever fires by monkeypatching?
# Wait, I'll just change `test_init3.py` to test standard sr listen.

import speech_recognition as sr
try:
    with engine.microphone as source:
        logging.info("Listening for 5 seconds for a single phrase (sr.record/listen)...")
        # Try a quick manual listen
        audio = engine.recognizer.listen(source, timeout=5, phrase_time_limit=5)
        text = engine.recognizer.recognize_google(audio)
        logging.info(f"Got: {text}")
except sr.WaitTimeoutError:
    logging.info("Timeout: No speech detected in 5 seconds.")
except sr.UnknownValueError:
    logging.info("Speech was detected but not understood.")
except Exception as e:
    logging.error(f"Error during listen: {e}")
