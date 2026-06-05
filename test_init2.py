import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
from modules.speech_recognition_engine import SpeechRecognitionEngine
from controller import Controller

logging.info("Initializing engine...")
engine = SpeechRecognitionEngine()
logging.info("Initializing controller...")
controller = Controller(engine)
logging.info("Controller initialized.")
