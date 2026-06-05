from modules.command_parser import CommandParser
import logging

logging.basicConfig(level=logging.INFO)

def test_new_features():
    parser = CommandParser()
    
    print("\n--- Testing Fuzzy Matching with Fillers ---")
    test_cases = [
        ("oh but google", "OPEN_APP", "google"),
        ("oh the calculator", "OPEN_APP", "calculator"),
        ("open google", "OPEN_APP", "google"),
        ("brightness up", "SYSTEM_CONTROL", "BRIGHTNESS_UP"),
        ("decrease brightness", "SYSTEM_CONTROL", "BRIGHTNESS_DOWN"),
        ("but the notepad", "OPEN_APP", "notepad")
    ]
    
    for text, expected_intent, expected_entity in test_cases:
        result = parser.parse(text)
        intent = result.get("intent")
        entity = result.get("entity")
        
        # Determine pass/fail
        intent_match = intent == expected_intent
        # Entity matching might be fuzzy or partial, but for these we expect clean extraction after stripping
        # "open google" -> entity "google"
        # "oh but google" -> corrected to "open google" -> entity "google"
        entity_match = expected_entity in str(entity) if entity else False
        
        status = "PASS" if intent_match and entity_match else "FAIL"
        print(f"Input: {text:<20} | Intent: {intent:<15} | Entity: {entity:<15} | {status}")

if __name__ == "__main__":
    test_new_features()
