import sys
import logging

logging.basicConfig(level=logging.INFO)

def check_brightness():
    print(f"Python Executable: {sys.executable}")
    try:
        import screen_brightness_control as sbc
        print(f"screen_brightness_control imported successfully: {sbc}")
        current = sbc.get_brightness()
        print(f"Current brightness: {current}")
    except ImportError as e:
        print(f"ImportError: {e}")
    except Exception as e:
        print(f"Error accessing brightness: {e}")

if __name__ == "__main__":
    check_brightness()
