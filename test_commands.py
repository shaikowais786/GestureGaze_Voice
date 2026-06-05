from modules.command_parser import CommandParser
import logging
import re

# logging.basicConfig(level=logging.DEBUG) 

def test_commands():
    print("Initializing CommandParser...")
    parser = CommandParser()
    
    test_cases = [
        ("search file report.txt", "SEARCH_FILE", "report.txt"),
        ("lock system", "SYSTEM_CONTROL", "LOCK_SYSTEM"),
        ("unknown command xyz", "UNKNOWN", None), # Should NOT match CONFIRMATION
        ("yes", "CONFIRMATION", "yes"), # Should match CONFIRMATION
    ]
    
    print(f"{'Input':<30} | {'Expected Intent':<15} | {'Expected Entity':<15} | {'Result':<10}")
    print("-" * 80)
    
    all_passed = True
    for text, expected_intent, expected_entity in test_cases:
        result = parser.parse(text)
        intent = result.get("intent")
        entity = result.get("entity")
        
        passed = (intent == expected_intent) and (entity == expected_entity)
        if not passed:
            all_passed = False
            
        status = "PASS" if passed else "FAIL"
        print(f"{text:<30} | {expected_intent:<15} | {str(expected_entity):<15} | {status:<10}")
        
        if not passed:
            print(f"  -> Got Intent: {intent}, Entity: {entity}")

    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    test_commands()
