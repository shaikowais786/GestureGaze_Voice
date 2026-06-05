from modules.command_parser import CommandParser
import pprint
import sys

def test_commands():
    parser = CommandParser()
    
    # Format: (input_text, expected_intent, expected_target, expected_destination_metadata)
    test_cases = [
        ("move file laptop in ball", "MOVE_FILE", "laptop", "ball"),
        ("move file laptop into ball", "MOVE_FILE", "laptop", "ball"),
        ("move file laptop inside ball", "MOVE_FILE", "laptop", "ball"),
        ("move file laptop and ball", "MOVE_FILE", "laptop", "ball"),
        ("move file laptop to the ball", "MOVE_FILE", "laptop", "ball"),
        ("move laptop to ball", "MOVE_FILE", "laptop", "ball"),
        ("microsoft word", "OPEN_APP", "microsoft word", None),
        ("microsoft excel", "OPEN_APP", "microsoft excel", None),
        ("microsoft powerpoint", "OPEN_APP", "microsoft powerpoint", None),
        ("word", "OPEN_APP", "word", None),
    ]
    
    failed = False
    for text, exp_intent, exp_target, exp_dest in test_cases:
        print(f"\n--- Testing: '{text}' ---")
        result = parser.parse(text)
        pprint.pprint(result)
        
        intent = result.get("intent")
        target = result.get("target")
        dest = result.get("metadata", {}).get("destination")
        
        if intent != exp_intent:
            print(f"FAIL: Expected intent '{exp_intent}', got '{intent}'")
            failed = True
        elif target != exp_target:
            print(f"FAIL: Expected target '{exp_target}', got '{target}'")
            failed = True
        elif exp_dest and dest != exp_dest:
            print(f"FAIL: Expected destination metadata '{exp_dest}', got '{dest}'")
            failed = True
        else:
            print("PASS")

    if failed:
        sys.exit(1)
    else:
        print("\nAll custom tests passed successfully!")

if __name__ == "__main__":
    test_commands()
