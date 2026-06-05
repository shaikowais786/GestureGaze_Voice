import sys
import os

# Ensure current directory is in sys.path
sys.path.append(os.getcwd())

try:
    from actions.action_manager import ActionManager
    from modules.speech_recognition_engine import SpeechRecognitionEngine
    print("Import successful for all modules!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
