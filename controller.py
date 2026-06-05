import time
import threading
import queue
import logging
import pyttsx3
from modules.command_parser import CommandParser
from modules.speaker_authentication import SpeakerAuthenticator
from security.user_manager import UserManager
from security.security_mode import SecurityMode
from actions.action_manager import ActionManager

class Controller:
    # States
    IDLE = "IDLE"
    LISTENING_WAKE_WORD = "LISTENING_WAKE_WORD" 
    AUTHENTICATING = "AUTHENTICATING"
    ACTIVE_COMMAND_MODE = "ACTIVE_COMMAND_MODE"
    CONFIRMATION_WAIT = "CONFIRMATION_WAIT"
    REGISTRATION_WAITING_FOR_NAME = "REGISTRATION_WAITING_FOR_NAME"

    def __init__(self, speech_engine):
        self.state = self.IDLE
        self.speech_engine = speech_engine
        
        # Initialize modules
        self.user_manager = UserManager()
        self.security_mode = SecurityMode()
        self.authenticator = SpeakerAuthenticator()
        self.parser = CommandParser()
        self.action_manager = ActionManager(self.security_mode)
        
        # TTS Engine
        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Runtime vars
        self.current_user = None
        self.authenticated = False
        self.low_confidence = False
        self.pending_action = None
        self.last_interaction_time = 0
        self.last_recognized_text = ""
        self.ignore_next_input = False
        self.is_speaking = False
        self.auth_retries = 0

    def _tts_worker(self):
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize() # Required for COM in background threads
        
        try:
            tts = win32com.client.Dispatch("SAPI.SpVoice")
            use_sapi = True
        except Exception as e:
            logging.error(f"SAPI initialization failed: {e}. Falling back to pyttsx3.")
            use_sapi = False
        
        while True:
            text = self.tts_queue.get()
            if text is None: break
            try:
                self.is_speaking = True
                if use_sapi:
                    tts.Speak(text)
                else:
                    tts_engine = pyttsx3.init()
                    tts_engine.setProperty('volume', 1.0)
                    tts_engine.say(text)
                    tts_engine.runAndWait()
                    del tts_engine
            except Exception as e:
                logging.error(f"TTS Error: {e}")
            finally:
                self.is_speaking = False
                    
            self.tts_queue.task_done()

    def speak(self, text):
        """Thread-safe TTS"""
        self.is_speaking = True
        logging.info(f"System speaks: {text}")
        self.tts_queue.put(text)

    def start(self):
        """Starts the single main synchronous listening loop."""
        self.state = self.LISTENING_WAKE_WORD
        logging.info(f"System started. State: {self.state}")
        self.speak("System ready. Listening for wake word.")
        
        import speech_recognition as sr
        import numpy as np
        
        # ⚡ OPTIMIZATION 2: KEEP DYNAMIC ENERGY THRESHOLD DISABLED
        self.speech_engine.recognizer.dynamic_energy_threshold = False
        logging.info(f"Microphone energy threshold (preserved): {self.speech_engine.recognizer.energy_threshold}")
            
        # 🧠 FIX 2: SINGLE MAIN LOOP LISTENER
        while True:
            # Pause main listening thread while user registration is recording voice print samples
            if getattr(self, 'state', self.IDLE) == "RECORDING_VOICE_SAMPLE":
                time.sleep(0.2)
                continue

            # Handle inactivity timeout if in active mode without confirmation
            if getattr(self, 'state', self.IDLE) == self.ACTIVE_COMMAND_MODE:
                if not getattr(self, 'waiting_for_confirmation', False):
                    last_time = getattr(self, 'last_interaction_time', None)
                    if last_time is not None and time.time() - last_time > 30:
                        logging.info("30 seconds inactivity.")
                        self.speak("System locking due to inactivity.")
                        self.state = self.LISTENING_WAKE_WORD
                        self.current_user = None
            
            # ⚡ OPTIMIZATION: SYSTEM TTS JOIN AWAIT
            self.tts_queue.join()
            while getattr(self, "is_speaking", False):
                time.sleep(0.05)
                
            if getattr(self, 'ignore_next_input', False):
                self.ignore_next_input = False
                continue

            if self.speech_engine.microphone is None:
                logging.error("No microphone configured.")
                time.sleep(1)
                continue

            with self.speech_engine.microphone as source:
                import sys
                sys.stdout.write("\rListening...                                      ")
                sys.stdout.flush()
                
                try:
                    # ⚡ OPTIMIZATION 10: DEBUG TIMING
                    process_start = time.time()
                    
                    audio = self.speech_engine.recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=4
                    )
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print("Mic error:", e)
                    continue

            try:
                # ⚡ OPTIMIZATION 10: PRINT TIMING
                print(f"Audio captured in: {time.time() - process_start:.2f}s")
                
                text = self.speech_engine.recognizer.recognize_google(audio).lower()
                print(f"\nRecognized: {text}")
                
                # Check for registration command first (so it doesn't get blocked by wake-word state)
                parsed = self.parser.parse(text)
                if parsed.get("intent") == "REGISTER_USER":
                    try:
                        raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                        audio_float = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    except:
                        audio_float = None
                    self.process_speech(text, audio_float)
                    continue

                # Execution routing extracted out. Main loop simply processes standard modes now.
                # 🧠 FIX 4: ADD FAST WAKE WORD CHECK
                if self.state in [self.LISTENING_WAKE_WORD, self.IDLE]:
                    if "voice" in text or "mode" in text:
                        try:
                            self.handle_wake_word(audio)
                        except: pass
                    else:
                        # Tell the user why their command was ignored (throttled to avoid spam)
                        now = time.time()
                        if now - getattr(self, '_last_wake_hint_time', 0) > 15:
                            self._last_wake_hint_time = now
                            print(f"[BLOCKED] Command '{text}' ignored — voice mode not active.")
                            self.speak("Say voice mode activate first.")
                    continue # Strict block: ignore all other input in wake word mode
                    
                if self.state == self.ACTIVE_COMMAND_MODE or self.state == self.REGISTRATION_WAITING_FOR_NAME:
                    # Normal processing
                    try:
                        raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                        audio_float = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    except:
                        audio_float = None
                        
                    self.process_speech(text, audio_float)

            except sr.UnknownValueError:
                pass
            except Exception as e:
                # 🧠 FAIL-SAFE SYSTEM
                import traceback
                traceback.print_exc()
                logging.error(f"Execution Error: {e}")
                self.speak("Something went wrong.")
                self.state = self.LISTENING_WAKE_WORD
                continue

    def process_speech(self, text, audio_data=None):
            
        if not text:
            return  
        # PRE-FILTER STRAY TTS ECHOES BEFORE PARSING
        # Sometimes the user speaks slightly before the speaker finishes an announcement
        # like "opening word", so Google transcribes "opening word create file...".
        # We must strip the echo out before parsing it so it doesn't get tricked!
        cleanup_echoes = [
            "opening word", "opening powerpoint", "opening excel", "opening file",
            "file deleted", "command not recognized", "powerpoint file created",
            "word file created", "excel file created", "python file created", "file created"
        ]
        clean_text = text.lower()
        for phrase in cleanup_echoes:
            clean_text = clean_text.replace(phrase, "").strip()
            
        if not clean_text:
            return
            
        # STATE: REGISTRATION_WAITING_FOR_NAME
        if self.state == self.REGISTRATION_WAITING_FOR_NAME:
            username = clean_text.strip()
            # Google API struggles with single words, so we STRICTLY ENFORCE "My name is..."
            if username.startswith("my name is "):
                username = username.replace("my name is ", "")
            else:
                self.speak("You must say: My name is, followed by your name.")
                return
                
            username = username.strip().title() # Capitalize first letter
            
            # Basic validation
            if len(username) > 20 or len(username.split()) > 3:
                 self.speak("Name too long. Please say a shorter name.")
                 return
            
            self.speak(f"Registering as {username}. Please repeat: The quick brown fox jumps over the lazy dog.")
            import threading
            t = threading.Thread(target=self._registration_workflow, args=(username,))
            t.start()
            self.state = "RECORDING_VOICE_SAMPLE"
            return

        # NORMAL PARSING (do not pass confirmation text to parser)
        parsed = self.parser.parse(clean_text)
        intent = parsed.get("intent")
        target = parsed.get("target")
        
        # COMMAND VALIDATION
        if intent is None:
            self.speak("Command not understood")
            return
            
        # 🧠 COMMAND ACCESS CONTROL
        PUBLIC_COMMANDS = ["REGISTER_USER", "VOICE_MODE", "WHO_AM_I", "COUNT_USERS"]
        
        if self.security_mode.is_enabled() and intent not in PUBLIC_COMMANDS:
             if not getattr(self, "authenticated", False):
                 self.speak("Unauthorized voice")
                 return
                 
        if intent not in PUBLIC_COMMANDS and intent != "SYSTEM_CONTROL":
            if not target or not target.strip():
                self.speak("Please specify properly")
                return
                
        # 🧠 PREVENT DUPLICATE EXECUTION
        if getattr(self, "last_intent", None) == intent and getattr(self, "last_target", None) == target:
            if time.time() - getattr(self, "last_execution_timestamp", 0) < 3.0:
                 return # Completely ignore identical commands fired consecutively within 3 seconds
                 
        self.last_intent = intent
        self.last_target = target
        self.last_execution_timestamp = time.time()
                
        # Update timer properly
        self.last_interaction_time = time.time()
        
        # 🧠 RESET SYSTEM (FAIL-SAFE)
        if text.lower() == "reset system":
            self.state = self.LISTENING_WAKE_WORD
            self.current_user = None
            self.speak("System reset.")
            return

        # STATE: LISTENING_WAKE_WORD / IDLE
        if self.state in [self.LISTENING_WAKE_WORD, self.IDLE]:
            if intent == "REGISTER_USER":
                self.handle_registration()
            elif intent == "DELETE_USER":
                self.speak("Voice mode is currently locked. Say voice mode activate before deleting your voice.")
            elif intent == "WHO_AM_I":
                self.speak("Voice mode is currently locked. Say voice mode activate.")
            elif intent == "VOICE_MODE":
                # User said the wake word. Authenticate 'who' is saying the wake word.
                self.handle_wake_word(audio_data)
            else:
                 # Command attempted without wake word
                 if self.security_mode.is_enabled():
                     self.speak("Voice not recognized. Secure mode is enabled. Please say voice mode activate.")
                 else:
                     self.handle_command(parsed, audio_data)
                     
        # STATE: ACTIVE_COMMAND_MODE
        elif self.state == self.ACTIVE_COMMAND_MODE:
            self.last_interaction_time = time.time() # Update activity timer
            
            if intent == "REGISTER_USER":
                self.handle_registration()
            elif intent == "DELETE_USER":
                self.handle_deletion()
            elif intent == "VOICE_MODE":
                # Allow a new user to steal the session if they say the wake word
                self.handle_wake_word(audio_data)
            elif intent == "WHO_AM_I":
                 if getattr(self, "authenticated", False):
                     self.speak(f"You are {self.current_user}")
                 else:
                     self.speak("You are a guest")
            elif intent == "COUNT_USERS":
                 count = len(self.user_manager.get_all_profiles())
                 if count == 0:
                     self.speak("There are no registered users")
                 elif count == 1:
                     self.speak("There is 1 registered user")
                 else:
                     self.speak(f"There are {count} registered users")
            elif intent == "CONFIRMATION":
                pass
            else:
                self.handle_command(parsed, audio_data)
                
        # State parsing below handles other modes

    def _authenticate_bg(self, audio_data, profiles):
        # ⚡ OPTIMIZATION 5: PARALLEL AUTHENTICATION THREAD
        import numpy as np
        try:
            raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            audio_float = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            embedding = self.authenticator.extract_embedding(audio_float)
        except Exception as e:
            logging.error(f"Failed to prepare audio buffer for background embedding: {e}")
            embedding = None

        if embedding is not None:
             result = self.authenticator.verify(embedding, profiles)
             score = result.get("confidence", 0.0)
             if score >= 0.65:
                 self.authenticated = True
                 self.current_user = result.get("username", "Unknown")
                 self.last_auth_time = time.time()
                 print(f"\n[AUTH SUCCESS] Verified as {self.current_user} in background. (Score: {score:.3f})")
             else:
                 self.authenticated = False
                 self.current_user = "Guest"
                 print(f"\n[AUTH FAILED] Background verification failed. (Score: {score:.3f})")
        else:
             self.authenticated = False
             
        self.is_authenticating = False

    def handle_wake_word(self, audio_data=None):
        logging.info("Wake word detected.")
        profiles = self.user_manager.get_all_profiles()
        
        # If no users registered, force them to register
        if not profiles:
            self.speak("No registered users. Please say register new user.")
            return

        if audio_data is None:
            self.speak("Could not capture voice for authentication. Try again.")
            return

        # ⚡ OPTIMIZATION 6: CACHE LAST AUTHENTICATED USER
        if getattr(self, "last_auth_time", 0) and time.time() - self.last_auth_time < 30:
             self.authenticated = True
             self.state = self.ACTIVE_COMMAND_MODE
             self.last_interaction_time = time.time()
             self.speak("Voice mode active")
             return

        self.authenticated = False # Default until background resolves
        self.current_user = "Guest"
        self.is_authenticating = True
        
        # ⚡ OPTIMIZATION 5: Trigger background authentication mapping safely
        threading.Thread(target=self._authenticate_bg, args=(audio_data, profiles)).start()
        
        # ⚡ OPTIMIZATION 7: SHORTEN WAKE RESPONSE
        self.speak("Voice mode active")
            
        self.state = self.ACTIVE_COMMAND_MODE
        self.last_interaction_time = time.time()

    def handle_registration(self):
        self.speak("Starting registration. To help me hear you clearly, please say: My name is, followed by your name.")
        self.state = self.REGISTRATION_WAITING_FOR_NAME

    def _registration_workflow(self, username):
        # Give TTS thread time to pick up the speech queue
        time.sleep(0.5)
        # Wait until the system finishes reading the instructions
        while self.is_speaking:
            time.sleep(0.1)
            
        # Add a tiny buffer so the user has time to take a breath
        time.sleep(0.5)

        # Capture 3 audio samples
        import numpy as np
        embeddings = []
        for i in range(3):
             self.speak(f"Capturing sample {i+1} of 3. Please speak for 5 seconds.")
             # Wait until TTS finishes so we don't capture the system's own voice
             while self.is_speaking:
                  time.sleep(0.1)
             
             logging.info(f"Starting registration recording {i+1}...")
             audio_data = self.speech_engine.get_audio_sample(duration=5)
             logging.info(f"Recording {i+1} complete.")
             
             if audio_data is not None:
                  emb = self.authenticator.extract_embedding(audio_data)
                  if emb is not None:
                       embeddings.append(emb)

        if len(embeddings) > 0:
             # Average embeddings
             avg_embedding = np.mean(embeddings, axis=0)
             self.user_manager.register_user(username, avg_embedding)
             self.speak(f"Registration successful. User ID {username} saved using {len(embeddings)} audio samples.")
             
             # Verify immediately against itself to check quality
             score = self.authenticator.verify_embedding(avg_embedding, avg_embedding)
             logging.info(f"Self-verification score for new user: {score}")
        else:
             self.speak("Registration failed. Could not record sufficient audio.")

        # Return to listening for the wake word after the workflow completes
        self.state = self.LISTENING_WAKE_WORD

    def handle_deletion(self):
        if getattr(self, "authenticated", False):
            self.user_manager.delete_user(self.current_user)
            self.speak(f"Voice profile for {self.current_user} has been permanently deleted. System linking reset.")
            self.current_user = None
            self.authenticated = False
            self.state = self.LISTENING_WAKE_WORD
        else:
            self.speak("Authentication required")

    def handle_command(self, parsed, audio_data=None):
        # 🚧 AWAIT BACKGROUND THREAD
        while getattr(self, "is_authenticating", False):
            time.sleep(0.05)
            
        intent = parsed.get("intent")
        if intent == "UNKNOWN":
            text = parsed.get("original_text", "").lower()
            if any(w in text for w in ["opening", "executed", "file created", "folder created", "file moved", "deleted"]):
                logging.info(f"Suppressed Command Not Recognized for TTS echo: {text}")
                return
                
            self.speak("Command not recognized.")
            return
            
        logging.info(f"Executing: {intent} -> {parsed.get('entity')}")
        
        result = self.action_manager.handle_command(parsed)
        
        if result.get("requires_confirmation"):
            # 🔒 DANGEROUS COMMAND — trigger synchronous confirmation
            self.pending_action = result["pending_action"]
            self.state = self.CONFIRMATION_WAIT
            self.speak(result["message"])
            self._run_confirmation()  # Blocks until resolved
            return
        
        if result.get("success"):
            self.speak(result["message"])
        else:
            self.speak(result.get("message", ""))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔒 CONFIRMATION SYSTEM (dangerous OS commands only)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _listen_for_confirmation(self):
        """ONE-SHOT mic capture for yes/no. Returns (text, audio) or (None/timeout, None)."""
        import speech_recognition as sr

        try:
            # Fresh mic + dedicated recognizer to avoid main-loop conflicts
            mic = sr.Microphone(
                device_index=self.speech_engine.microphone.device_index if self.speech_engine.microphone else None,
                sample_rate=16000
            )
            rec = sr.Recognizer()
            rec.dynamic_energy_threshold = False
            rec.pause_threshold = 1.2
            rec.energy_threshold = self.speech_engine.recognizer.energy_threshold

            with mic as source:
                import sys
                sys.stdout.write(f"\r[CONFIRM] Listening for yes/no (threshold={int(rec.energy_threshold)})...")
                sys.stdout.flush()

                audio = rec.listen(source, timeout=8, phrase_time_limit=5)
                text = rec.recognize_google(audio).lower()
                return text, audio

        except sr.WaitTimeoutError:
            return "timeout", None
        except sr.UnknownValueError:
            return None, None
        except Exception as e:
            logging.error(f"Confirmation listen error: {e}")
            return None, None

    def _run_confirmation(self):
        """Synchronous confirmation flow — blocks main loop, one attempt + one retry."""
        YES_WORDS = ["yes", "yeah", "yep", "confirm", "do it", "sure", "yas", "yah", "ya"]
        NO_WORDS  = ["no", "cancel", "stop", "don't", "nah", "nope", "na"]

        for attempt in range(2):
            if attempt == 1:
                self.speak("Please say yes or no.")

            # Wait for TTS to finish before opening mic
            self.tts_queue.join()
            while self.is_speaking:
                time.sleep(0.05)
            time.sleep(0.3)  # buffer so mic doesn't catch TTS tail

            text, audio = self._listen_for_confirmation()
            print(f"\n[CONFIRM INPUT]: {text}")

            if text == "timeout":
                self.speak("Confirmation timed out.")
                break

            if text is None:
                continue  # unintelligible — retry

            if any(w in text for w in YES_WORDS):
                self._execute_pending_action()
                self.pending_action = None
                self.state = self.LISTENING_WAKE_WORD
                return

            if any(w in text for w in NO_WORDS):
                self.speak("Operation cancelled.")
                break

            # Unrecognized word — retry
            continue

        # Fell through: timeout, cancel, or failed retries
        self.pending_action = None
        self.state = self.LISTENING_WAKE_WORD

    def _execute_pending_action(self):
        """Execute the stored pending_action (dangerous system commands)."""
        action = self.pending_action
        if not action:
            return

        logging.info(f"Executing confirmed action: {action}")

        result = self.action_manager.handle(
            action.get("intent"),
            action.get("target"),
            action.get("metadata")
        )
        self.speak(result.get("message", "Executed."))
