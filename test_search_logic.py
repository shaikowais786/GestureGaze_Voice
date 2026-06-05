import os
import shutil
import logging
from actions.file_controller import FileController

logging.basicConfig(level=logging.INFO)

def test_search():
    # Setup test environment
    test_root = os.path.join(os.getcwd(), "test_search_env")
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    
    os.makedirs(os.path.join(test_root, "Documents"))
    os.makedirs(os.path.join(test_root, "Downloads"))
    
    # Create dummy files
    files_to_create = [
        os.path.join(test_root, "Documents", "Final Exam.pdf"),
        os.path.join(test_root, "Downloads", "project_v2.docx"),
        os.path.join(test_root, "Downloads", "irrelevant_file.txt")
    ]
    
    for f in files_to_create:
        with open(f, "w") as f_handle:
            f_handle.write("dummy content")

    # Initialize Controller with custom test path
    controller = FileController(desktop_path=test_root)
    
    print("\n--- Testing File Search ---")
    
    # Test 1: Exact-ish match (ignoring case/extension)
    result = controller.search_file("final exam")
    if result and "Final Exam.pdf" in result:
        print("Test 1 (final exam): PASS")
    else:
        print(f"Test 1 (final exam): FAIL - Found {result}")

    # Test 2: Partial match
    result = controller.search_file("project")
    if result and "project_v2.docx" in result:
        print("Test 2 (project): PASS")
    else:
        print(f"Test 2 (project): FAIL - Found {result}")

    # Test 3: Non-existent
    result = controller.search_file("missing_file_123")
    if result is None:
        print("Test 3 (missing): PASS")
    else:
        print(f"Test 3 (missing): FAIL - Found {result}")

    # Cleanup
    shutil.rmtree(test_root)

if __name__ == "__main__":
    test_search()
