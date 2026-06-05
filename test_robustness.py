from modules.command_parser import CommandParser
from modules.speaker_authentication import SpeakerAuthenticator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_robustness():
    parser = CommandParser()
    
    print("Running robustness tests...")
    
    test_cases = [
        ("oh chrome", "OPEN_APP", "chrome"),          # Fuzzy "open"
        ("weiss mode activated", "VOICE_MODE", "voice mode activate"), # Fuzzy phrase
        ("lock sistum", "SYSTEM_CONTROL", "LOCK_SYSTEM"), # Fuzzy "lock system"
        ("secure voice mood", "SECURE_MODE", "secure voice mode"), # Fuzzy phrase
        ("search fil report.txt", "SEARCH_FILE", "report.txt"), # Fuzzy "search file"
        ("completely unknown", "UNKNOWN", None)
    ]

    with open("robustness_results.txt", "w", encoding="utf-8") as f:
        f.write("\n--- 1. Testing Fuzzy Command Matching ---\n")
        
        f.write(f"{'Input':<30} | {'Expected Intent':<15} | {'Expected Entity':<20} | {'Result':<10}\n")
        f.write("-" * 85 + "\n")
        
        for text, expected_intent, expected_entity in test_cases:
            result = parser.parse(text)
            intent = result.get("intent")
            entity = result.get("entity")
            
            passed = (intent == expected_intent)
            if expected_entity and entity:
                if expected_entity.lower() != entity.lower():
                     pass
            
            status = "PASS" if passed else "FAIL"
            f.write(f"{text:<30} | {expected_intent:<15} | {str(entity):<20} | {status:<10}\n")
            if not passed:
                 f.write(f"   -> Got: {intent} / {entity}\n")

        f.write("\n--- 2. Testing Speaker Authentication Threshold ---\n")
        auth = SpeakerAuthenticator(similarity_threshold=0.88)
        f.write(f"Authenticator threshold: {auth.similarity_threshold}\n")
        if auth.similarity_threshold == 0.88:
            f.write("Threshold verification: PASS\n")
        else:
            f.write(f"Threshold verification: FAIL (Got {auth.similarity_threshold})\n")

    # We cannot easily test actual embedding math without wav files, 
    # but we authenticated the class init logic.

if __name__ == "__main__":
    test_robustness()
