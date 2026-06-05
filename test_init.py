import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logging.info("Testing speech engine import")
from modules.speech_recognition_engine import SpeechRecognitionEngine
logging.info("Imported speech engine")
engine = SpeechRecognitionEngine()
logging.info("Initialized engine")
