import speech_recognition as sr
import pyaudio
import numpy as np

MICS_TO_TEST = [1, 5, 9, 11] # Indices of inputs from list_mic_devices.py

print("Testing microphones to find which one hears you...")
print("Please SPEAK CONTINUOUSLY for the next 10 seconds!")

best_mic = None
highest_energy = 0

for idx in MICS_TO_TEST:
    try:
        recognizer = sr.Recognizer()
        print(f"\n--- Testing Mic Index [{idx}] ---")
        mic = sr.Microphone(device_index=idx)
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(f"Index [{idx}] ambient energy: {recognizer.energy_threshold:.2f}")
            print(f"Listening to [{idx}] for 2 seconds...")
            # We just want raw amplitude
            audio = recognizer.record(source, duration=2.0)
            raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            audio_array = np.frombuffer(raw_data, dtype=np.int16)
            
            # Calculate max amplitude
            max_amp = np.max(np.abs(audio_array))
            print(f"Index [{idx}] Max Volume: {max_amp}")
            
            if max_amp > highest_energy:
                highest_energy = max_amp
                best_mic = idx
    except Exception as e:
        print(f"Could not test Mic [{idx}]: {e}")

print("\n===============================")
if best_mic is not None and highest_energy > 500:
    print(f"✅ The active microphone appears to be Index [{best_mic}] with Volume {highest_energy}")
else:
    print("❌ No microphone picked up significant sound. Are you muted?")
print("===============================")
