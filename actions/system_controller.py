import pyautogui
import logging
import os
import datetime

class SystemController:
    def __init__(self):
        # Fail-safe to prevent mouse locking content
        pyautogui.FAILSAFE = True

    def execute(self, action):
        """
        Executes system-level commands using pyautogui.
        """
        logging.info(f"SystemController executing raw action: {action}")
        
        # Normalize fuzzy text strings to system constants
        if isinstance(action, str):
            action = action.upper().replace(" ", "_")
        
        logging.info(f"SystemController parsing as: {action}")
        
        try:
            if action == "VOLUME_UP":
                pyautogui.press("volumeup")
            elif action == "VOLUME_DOWN":
                pyautogui.press("volumedown")
            elif action == "MUTE" or action == "UNMUTE":
                pyautogui.press("volumemute")
            elif action == "PLAY" or action == "PAUSE":
                pyautogui.press("playpause")
            elif action == "NEXT":
                pyautogui.press("nexttrack")
            elif action == "PREVIOUS":
                pyautogui.press("prevtrack")
            elif action == "CLOSE_WINDOW":
                pyautogui.hotkey("alt", "f4")
            elif action == "MINIMIZE_WINDOW":
                pyautogui.hotkey("win", "down")
            elif action == "TASK_MANAGER":
                import subprocess
                subprocess.Popen("start taskmgr", shell=True)
            elif action == "LOCK_SYSTEM":
                pyautogui.hotkey("win", "l")
            elif action == "SHUTDOWN":
                # Uncomment to enable actual shutdown:
                os.system("shutdown /s /t 1")
                logging.warning("Shutdown command executed")
            elif action == "BRIGHTNESS_UP":
                try:
                    import screen_brightness_control as sbc
                    current = sbc.get_brightness()
                    # get_brightness returns a list of values for each monitor. specific to windows/linux behavior
                    # typically we just take the first or verify structure
                    if isinstance(current, list):
                        new_val = min(current[0] + 10, 100)
                    else:
                        new_val = min(current + 10, 100)
                    sbc.set_brightness(new_val)
                    logging.info(f"Increased brightness to {new_val}%")
                except ImportError:
                    logging.error("screen_brightness_control not installed.")
                except Exception as e:
                    logging.error(f"Failed to change brightness: {e}")
            elif action == "BRIGHTNESS_DOWN":
                try:
                    import screen_brightness_control as sbc
                    current = sbc.get_brightness()
                    if isinstance(current, list):
                        new_val = max(current[0] - 10, 0)
                    else:
                        new_val = max(current - 10, 0)
                    sbc.set_brightness(new_val)
                    logging.info(f"Decreased brightness to {new_val}%")
                except ImportError:
                    logging.error("screen_brightness_control not installed.")
                except Exception as e:
                    logging.error(f"Failed to change brightness: {e}")
            elif action == "SCREENSHOT":
                file_path = self.take_screenshot()
                if not file_path:
                    return False
            else:
                logging.warning(f"Unknown system action: {action}")
                return False
            
            return True
        except Exception as e:
            logging.error(f"System action failed: {e}")
            return False

    def take_screenshot(self):
        """
        Captures the screen and saves it to the user's Pictures/Screenshots folder.
        Returns the path to the saved screenshot if successful, else None.
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"Screenshot_{timestamp}.png"
            
            # Default path: Users/{user}/Pictures/Screenshots
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
            
            # Create directory if it doesn't exist
            if not os.path.exists(pictures_dir):
                os.makedirs(pictures_dir)
                
            filepath = os.path.join(pictures_dir, filename)
            
            logging.info(f"Taking screenshot: {filepath}")
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            return filepath
        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")
            return None
