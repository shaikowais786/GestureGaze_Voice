from modules.command_parser import CommandParser
import logging

logging.basicConfig(level=logging.INFO)

def test_registration_robustness():
    parser = CommandParser()
    
    print("\n--- Testing Registration Trigger ---")
    
    test_cases = [
        ("register new user", "REGISTER_USER"),
        ("register my voice", "REGISTER_USER"),
        ("regester my voice", "REGISTER_USER"), # Fuzzy check
        ("i want to register my voice", "REGISTER_USER"), # Phrase check
        ("easter new user", "REGISTER_USER"),
        ("christian new user", "REGISTER_USER")
    ]
    
    for text, expected_intent in test_cases:
        result = parser.parse(text)
        intent = result.get("intent")
        status = "PASS" if intent == expected_intent else "FAIL"
        print(f"Input: {text:<30} | Intent: {intent:<15} | {status}")

if __name__ == "__main__":
    test_registration_robustness()
