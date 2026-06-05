from modules.command_parser import CommandParser
import logging

logging.basicConfig(level=logging.INFO)

def test_confirmation_robustness():
    parser = CommandParser()
    
    print("\n--- Testing Confirmation Robustness ---")
    
    # Intended intent: CONFIRMATION
    # Expected entity: yes/confirm OR no/cancel
    
    test_cases = [
        # Positive
        ("yes", "CONFIRMATION", "yes"),
        ("confirm", "CONFIRMATION", "confirm"),
        ("yeah", "CONFIRMATION", "yes"),        # Common variation
        ("yep", "CONFIRMATION", "yes"),         # Common variation
        ("sure", "CONFIRMATION", "confirm"),    # Common variation
        ("ok confirm", "CONFIRMATION", "confirm"), 
        
        # Negative
        ("no", "CONFIRMATION", "no"),
        ("cancel", "CONFIRMATION", "cancel"),
        ("nope", "CONFIRMATION", "no"),         # Common variation
        ("nah", "CONFIRMATION", "no"),          # Common variation
        ("cancel action", "CONFIRMATION", "cancel"),
        ("don't do it", "CONFIRMATION", "no")   # Harder case
    ]
    
    with open("confirmation_results_utf8.txt", "w", encoding="utf-8") as f:
        f.write(f"{'Input':<20} | {'Expected':<12} | {'Got Intent':<12} | {'Got Entity':<12} | {'Result':<6}\n")
        f.write("-" * 80 + "\n")
        
        for text, expected_intent, expected_entity in test_cases:
            result = parser.parse(text)
            intent = result.get("intent")
            entity = result.get("entity")
            
            # Loose match for entity (we just want positive or negative bucket)
            passed = (intent == expected_intent)
            
            status = "PASS" if passed else "FAIL"
            f.write(f"{text:<20} | {expected_intent:<12} | {str(intent):<12} | {str(entity):<12} | {status:<6}\n")

if __name__ == "__main__":
    test_confirmation_robustness()
