import logging
import sys
import os

# Configure Logging before PyAudio/PyTTSX3 override it
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("system.log")
    ]
)

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import threading
from controller import Controller
from modules.speech_recognition_engine import SpeechRecognitionEngine

def main():
    logging.info("Initializing GestureGaze_Voice System...")

    # Initialize Speech Engine
    # We pass the model path explicitly or rely on default
    speech_engine = SpeechRecognitionEngine()

    # Initialize Controller
    controller = Controller(speech_engine)

    try:
        # Start the system
        # This will block in the speech recognition loop
        controller.start()
    except KeyboardInterrupt:
        logging.info("Stopping system...")
        speech_engine.stop()
        sys.exit(0)
    except Exception as e:
        logging.critical(f"System crashed: {e}")
        speech_engine.stop()
        raise

if __name__ == "__main__":
    main()
