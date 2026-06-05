import speech_recognition as sr
import wave
import time

print("Initializing mic...")
recognizer = sr.Recognizer()
mic = sr.Microphone()

try:
    with mic as source:
        print("Calibrating background noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print(f"Energy threshold is now {recognizer.energy_threshold}")
        
        print("Listening for 5 seconds...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        print("Processing audio data...")
        raw_data = audio.get_raw_data()
        
        with wave.open("debug_test.wav", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2) # 16-bit
            f.setframerate(16000)
            f.writeframes(raw_data)
        
        print(f"Wrote {len(raw_data)} bytes. Try recognizing...")
        try:
            text = recognizer.recognize_google(audio)
            print("Google recognized:", text)
        except sr.UnknownValueError:
            print("Google could not understand audio.")
        except sr.RequestError as e:
            print("Google error:", e)

except sr.WaitTimeoutError:
    print("No speech detected within 5 seconds.")
except Exception as e:
    print("Error:", e)
