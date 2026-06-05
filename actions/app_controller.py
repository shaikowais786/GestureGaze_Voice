import os
import subprocess
import logging
from difflib import get_close_matches

class AppController:
    # 🧠 NORMALIZE APP NAMES
    # RULE: ALL commands MUST use "start" prefix to open in a NEW window/process.
    # Without "start", CLI apps (powershell, cmd, python) hijack the Python console.
    # For GUI apps, "start" is harmless and ensures clean process separation.
    APP_ALIASES = {
        # ── Browsers ──────────────────────────────────────────────────────
        "chrome": "start chrome",
        "google": "start chrome",
        "google chrome": "start chrome",
        "edge": "start msedge",
        "microsoft edge": "start msedge",
        "firefox": "start firefox",

        # ── Office ────────────────────────────────────────────────────────
        "word": "start winword",
        "excel": "start excel",
        "powerpoint": "start powerpnt",
        "microsoft word": "start winword",
        "microsoft excel": "start excel",
        "microsoft powerpoint": "start powerpnt",
        "outlook": 'start outlook',
        "onenote": "start onenote",
        "one note": "start onenote",
        "teams": "start msteams:",

        # ── System Tools ──────────────────────────────────────────────────
        "calculator": "start calc",
        "calc": "start calc",
        "notepad": "start notepad",
        "paint": "start mspaint",
        "ms paint": "start mspaint",
        "explorer": "start explorer",
        "file explorer": "start explorer",
        "task manager": "start taskmgr",
        "control panel": "start control",
        "settings": "start ms-settings:",
        "snipping tool": "start snippingtool",

        # ── Terminal / CLI Apps (MUST use "start" for new window) ─────────
        "cmd": "start cmd",
        "command prompt": "start cmd",
        "powershell": "start powershell",
        "terminal": "start wt",
        "python": "start python",
        "wsl": "start wsl",
        "git bash": 'start "" "C:\\Program Files\\Git\\git-bash.exe"',

        # ── Dev Tools ─────────────────────────────────────────────────────
        "code": "start code",
        "vs code": "start code",
        "visual studio code": "start code",
        "visual studio": "start devenv",
        "android studio": "start studio64",

        # ── Media & Web Apps ──────────────────────────────────────────────
        "camera": "start microsoft.windows.camera:",
        "photos": "start ms-photos:",
        "spotify": "start spotify:",
        "whatsapp": "start whatsapp:",
        "what's up": "start whatsapp:",
        "var sab": "start whatsapp:",

        # ── Windows Utilities ─────────────────────────────────────────────
        "clock": "start ms-clock:",
        "calendar": "start outlookcal:",
        "weather": "start bingweather:",
        "sound recorder": "start ms-soundrecorder:",
        "phone link": "start ms-phone:",
        "sticky notes": "start ms-stickynotes:",
        "store": "start ms-windows-store:",
        "microsoft store": "start ms-windows-store:",
        "account": "start ms-settings:accounts",
        "my account": "start ms-settings:accounts",
    }

    def launch_app(self, app_name):
        """
        Launches an application by fuzzy matching its alias.
        """
        if not app_name:
            return False, "Application name missing", None

        app_name_lower = app_name.lower().strip()
        
        # 1. Try exact match first
        if app_name_lower in self.APP_ALIASES:
            app_key = app_name_lower
            cmd = self.APP_ALIASES[app_key]
        else:
            # 2. Fuzzy match fallback
            best_match = get_close_matches(app_name_lower, self.APP_ALIASES.keys(), n=1, cutoff=0.6)
            if best_match:
                app_key = best_match[0]
                cmd = self.APP_ALIASES[app_key]
            else:
                logging.warning(f"Application not found for: {app_name_lower}")
                return False, "Application not found", None

        # 🧠 DEBUG LOG
        print(f"App requested: {app_name_lower}")
        print(f"Matched app: {app_key}")
        print(f"Command: {cmd}")
        
        logging.info(f"App requested: {app_name_lower}")
        logging.info(f"Matched app: {app_key}")
        logging.info(f"Command: {cmd}")
        
        # 🧠 SAFE EXECUTION — detach from Python's console
        try:
            subprocess.Popen(
                cmd, 
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True, f"Opening {app_key}", app_key
        except Exception as e:
            print("App launch error:", e)
            return False, "Failed to open application", app_key
