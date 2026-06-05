import re
import logging
import difflib

class CommandParser:
    """
    Unified voice command parser — single source of truth for all intents.
    Returns structured dicts: {intent, entity, target, metadata, original_text}

    Priority order for disambiguation:
    1. Security / Wake Word
    2. File System Commands
    3. System Control
    4. Media Control
    5. App Control
    """

    # Filler words stripped from the front of every utterance
    FILLERS = [
        r"^please\b", r"^okay\b", r"^ok\b", r"^hey\b", r"^hi\b",
        r"^system\b", r"^computer\b", r"^can you\b", r"^bro\b",
        r"^yo\b", r"^uh\b", r"^um\b", r"^oh\b", r"^but\b",
        r"^the\b", r"^a\b", r"^an\b"
    ]

    # File type → extension map (used by parser to build metadata)
    FILE_TYPE_MAP = {
        "word": ".docx",
        "excel": ".xlsx",
        "text": ".txt",
        "powerpoint": ".pptx",
        "power point": ".pptx",
        "power": ".pptx",
        "pp": ".pptx",
        "image": ".png",
        "zip": ".zip",
        "zi": ".zip",
        "python": ".py",
        "html": ".html",
        "pdf": ".pdf",
        "doc": ".docx",
    }

    def __init__(self):
        # ── 1. SECURITY ─────────────────────────────────────────────────────
        self._security_patterns = {
            "SECURE_MODE":   [r"(secure voice mode)"],
            "VOICE_MODE":    [r"(voice mode activate)", r".*(voice mode).*", r".*(mode activ).*", r".*(more doctor).*", r".*(voice mod).*"],
            "REGISTER_USER": [r"(reg[ie]ster\s+new\s+user)", r"(reg[ie]ster\s+my\s+voice)", r".*(reg[ie]ster\s+voice).*", r"(easter\s+new\s+user)", r"(christian\s+new\s+user)"],
            "DELETE_USER":   [r"(delete|remove|clear)\s+my\s+voice", r"(delete|remove|clear)\s+user"],
            "WHO_AM_I":      [r"(who am i)", r"(who is speaking)", r"(what is my name)", r"(identify user)"],
            "COUNT_USERS":   [r"(how many user)", r"(how many users)", r"(user count)", r"(how many profiles)"],
            "CONFIRMATION":  [r"\b(yes)\b", r"\b(yeah)\b", r"\b(yep)\b", r"\b(sure)\b",
                              r"\b(no)\b",  r"\b(nah)\b",  r"\b(nope)\b", r"\b(don't)\b", r"\b(dont)\b", r"\b(do not)\b", r"\b(stop)\b",
                              r"\b(confirm)\b", r"\b(cancel)\b"],
        }

        self.KNOWN_APPS = {
            "chrome", "google", "google chrome", "edge", "microsoft edge", "firefox",
            "word", "excel", "powerpoint", "outlook", "onenote", "one note", "teams",
            "calculator", "calc", "notepad", "paint", "ms paint", "explorer", "file explorer",
            "task manager", "control panel", "settings", "snipping tool", "cmd", "command prompt",
            "powershell", "terminal", "python", "wsl", "git bash", "code", "vs code",
            "visual studio code", "visual studio", "android studio", "camera", "photos",
            "spotify", "whatsapp", "what's up", "var sab", "clock", "calendar", "weather",
            "sound recorder", "phone link", "sticky notes", "store", "microsoft store",
            "account", "my account", "microsoft word", "microsoft excel", "microsoft powerpoint"
        }

        # ── 2. FILE SYSTEM ───────────────────────────────────────────────────
        # ALL patterns MUST be ^-anchored because _match_group uses re.search,
        # which can find partial matches mid-string (e.g. "search file X" matching OPEN_FILE)
        self._file_patterns = {
            "OPEN_IN_VSCODE":[r"^open\s+(.+)\s+in\s+(?:vscode|code|vs code)"],
            "OPEN_FOLDER":   [
                r"^open\s+folder\s+(?P<name>.+)$",
                r"^open\s+folder$",
                r"^(?:open|read)\s+(?:folder|directory)\s+(?P<name>.+?)$",
            ],
            "CREATE_FOLDER": [r"^(?:create|new)\s+folder\s+(?P<name>.+)$"],
            "MOVE_FILE":     [r"^move\s+(?:file\s+)?(?P<name>.+?)\s+(?:to\s+the|to|in|into|inside|and)\s+(?P<destination>.+)$"],
            "DELETE_FILE":   [r"^delete\s+(?:file\s+)?(?P<name>.+?)(?:\s+in\s+(?P<type>[\w\s]+))?$"],
            "CREATE_FILE":   [r"^create\s+(?:file\s+)?(?P<name>.+?)(?:\s+in\s+(?P<type>[\w\s]+))?$"],
            "SEARCH_FILE":   [r"^search\s+(?:for\s+)?(?:file\s+)?(?P<name>.+?)(?:\s+in(?:side)?\s+(?P<type>[\w\s]+))?$"],
            "OPEN_FILE":     [
                r"^(?:open|read)\s+file\s+(?P<name>.+?)\s+inside\s+(?P<parent>[\w\s]+)$",
                r"^(?:open|read)\s+file\s+(?P<name>.+?)(?:\s+in\s+(?P<type>[\w\s]+))?$",
                r"^(?P<name>(?!file\s+).+?)\s+in\s+(?P<type>word|excel|powerpoint|power point|power|pp|text|image|zip|python|pdf|doc|html)$",
            ],
        }

        # ── 3. SYSTEM CONTROL ────────────────────────────────────────────────
        self._system_patterns = {
            "SYSTEM_CONTROL": [
                r"(volume up)", r"(increase volume)", r"(louder)", r"(make it louder)",
                r"(volume down)", r"(decrease volume)", r"(quieter)", r"(make it quieter)",
                r"(mute audio)", r"(silence)", r"(shut up)", r"\b(mute)\b",
                r"(unmute audio)", r"(restore volume)", r"\b(unmute)\b",
                r"(close window)", r"(minimize window)", r"(minimise window)",
                r"(task manager)",
                r"(shutdown)", r"(shut down)",
                r"(lock system)",
                r"(brightness up)", r"(increase brightness)", r"(brighter)", r"(make it brighter)",
                r"(brightness down)", r"(decrease brightness)", r"(dimmer)", r"(dim screen)",
                r"(take screenshot)", r"(screenshot)", r"(capture screen)", r"(print screenshot)",
                r".*(excrete).*", r".*(screen.*shot).*",
            ],
        }

        # ── 4. MEDIA CONTROL ─────────────────────────────────────────────────
        self._media_patterns = {
            "SYSTEM_CONTROL": [
                r"(play music)", r"\b(play)\b", r"\b(resume)\b",
                r"\b(pause)\b", r"(stop music)", r"\b(stop)\b",
                r"(next track)", r"\b(next)\b", r"\b(skip)\b",
                r"(previous track)", r"(previous)", r"(back track)",
            ],
        }

        # ── 5. APP CONTROL ───────────────────────────────────────────────────
        self._app_patterns = {
            "OPEN_APP": [
                r"^(?:open|start|launch)?\s*(?P<name>.+)$",
            ],
        }

        # Normalized system-control action map
        self._sys_action_map = {
            "volume up": "VOLUME_UP", "increase volume": "VOLUME_UP",
            "louder": "VOLUME_UP", "make it louder": "VOLUME_UP",
            "volume down": "VOLUME_DOWN", "decrease volume": "VOLUME_DOWN",
            "quieter": "VOLUME_DOWN", "make it quieter": "VOLUME_DOWN",
            "mute": "MUTE", "mute audio": "MUTE", "silence": "MUTE", "shut up": "MUTE",
            "unmute": "UNMUTE", "unmute audio": "UNMUTE", "restore volume": "UNMUTE",
            "play": "PLAY", "play music": "PLAY", "resume": "PLAY",
            "pause": "PAUSE", "stop": "PAUSE", "stop music": "PAUSE",
            "next": "NEXT", "next track": "NEXT", "skip": "NEXT",
            "previous": "PREVIOUS", "previous track": "PREVIOUS", "back track": "PREVIOUS",
            "close window": "CLOSE_WINDOW", "minimize window": "MINIMIZE_WINDOW",
            "minimise window": "MINIMIZE_WINDOW", "minimize": "MINIMIZE_WINDOW", "minimise": "MINIMIZE_WINDOW",
            "task manager": "TASK_MANAGER",
            "lock system": "LOCK_SYSTEM",
            "shutdown": "SHUTDOWN", "shut down": "SHUTDOWN",
            "brightness up": "BRIGHTNESS_UP", "increase brightness": "BRIGHTNESS_UP",
            "brighter": "BRIGHTNESS_UP", "make it brighter": "BRIGHTNESS_UP",
            "brightness down": "BRIGHTNESS_DOWN", "decrease brightness": "BRIGHTNESS_DOWN",
            "dimmer": "BRIGHTNESS_DOWN", "dim screen": "BRIGHTNESS_DOWN",
            "take screenshot": "SCREENSHOT", "screenshot": "SCREENSHOT",
            "capture screen": "SCREENSHOT", "print screenshot": "SCREENSHOT",
            "excrete": "SCREENSHOT",
        }

    # ─────────────────── PUBLIC API ───────────────────────────────────────────

    def parse(self, text: str) -> dict:
        """
        Parse a spoken utterance and return a structured result dict:
        {
            "intent":        str,
            "entity":        str | None,   # backwards-compat alias to `target`
            "target":        str | None,   # primary cleaned value
            "metadata":      dict,         # e.g. {"file_type": "word", "ext": ".docx"}
            "original_text": str,
        }
        """
        original_text = text
        
        # 🧠 STEP 1: CLEAN INPUT BEFORE MATCHING
        text = text.lower().strip()
        
        # Repeatedly strip leading fillers (anchored to start)
        old_text = None
        while text != old_text:
            old_text = text
            for pattern in self.FILLERS:
                text = re.sub(pattern, "", text).strip()
            
        # Audio artifacts fixes
        text = text.replace("intext", "in text").replace("inword", "in word").replace("inexcel", "in excel").replace("inpowerpoint", "in powerpoint")

        # Spelling / phonetic normalization
        text = re.sub(r"\bsistum\b", "system", text)
        text = re.sub(r"\bvoice mood\b", "voice mode", text)
        text = re.sub(r"\bfil\b", "file", text)

        # Normalize variations
        if "shut up" in text: text = text.replace("shut up", "mute")
        if "make it louder" in text: text = text.replace("make it louder", "volume up")
        if "make it quieter" in text: text = text.replace("make it quieter", "volume down")
        if "power off" in text: text = text.replace("power off", "shutdown")
        
        # Priority 1 — Security (Check immediately after cleaning to avoid synonym replacements)
        result = self._match_group(self._security_patterns, text)
        if result:
            return self._finalize(result, text)
        
        # 🧠 STEP 2: STRICT INTENT MATCHING (System Controls)
        sys_target = None
        if any(w in text for w in ["volume up", "increase volume", "louder"]): sys_target = "VOLUME_UP"
        elif any(w in text for w in ["volume down", "decrease volume", "quieter"]): sys_target = "VOLUME_DOWN"
        elif any(w in text for w in ["mute", "silence"]): sys_target = "MUTE"
        elif any(w in text for w in ["unmute", "restore volume"]): sys_target = "UNMUTE"
        elif any(w in text for w in ["brightness up", "brighter"]): sys_target = "BRIGHTNESS_UP"
        elif any(w in text for w in ["brightness down", "dimmer"]): sys_target = "BRIGHTNESS_DOWN"
        elif any(w in text for w in ["screenshot", "capture screen", "print screen", "excrete"]): sys_target = "SCREENSHOT"
        elif any(w in text for w in ["close window"]): sys_target = "CLOSE_WINDOW"
        elif any(w in text for w in ["minimize window"]): sys_target = "MINIMIZE_WINDOW"
        elif "task manager" in text: sys_target = "TASK_MANAGER"
        elif "shutdown" in text: sys_target = "SHUTDOWN"
        
        if sys_target:
            return {"intent": "SYSTEM_CONTROL", "target": sys_target, "entity": sys_target, "metadata": {"action": sys_target}, "original_text": original_text}
            
        # 🧠 MEDIA CONTROL SAFEGUARDS (Strict Detection)
        if len(text.split()) <= 5:
            media_target = None
            if re.search(r"\b(play music|resume|play)\b", text): media_target = "PLAY"
            elif re.search(r"\b(pause|stop music|stop)\b", text): media_target = "PAUSE"
            elif re.search(r"\b(next track|skip|next)\b", text): media_target = "NEXT"
            elif re.search(r"\b(previous track|back track|previous)\b", text): media_target = "PREVIOUS"
            
            if media_target:
                return {"intent": "SYSTEM_CONTROL", "target": media_target, "entity": media_target, "metadata": {"action": media_target}, "original_text": original_text}
        
        # 🧠 STEP 2: NORMALIZE COMMANDS FOR OTHER INTENTS (negative lookbehind for dot)
        ACTION_MAP = {
            "delete": ["remove", "erase"],
            "open": ["launch", "start", "read"],
            "create": ["make", "generate", "new"],
            "search": ["find", "look for"]
        }
        FILE_TYPE_MAP = {
            "word": ["doc", "document"],
            "excel": ["sheet"],
            "powerpoint": ["ppt", "slides", "power", "pp"],
            "text": ["txt"]
        }
        for key, values in ACTION_MAP.items():
            for v in values:
                text = re.sub(rf"(?<!\.)\b{v}\b", key, text)

        for key, values in FILE_TYPE_MAP.items():
            for v in values:
                text = re.sub(rf"(?<!\.)\b{v}\b", key, text)
                
        text = re.sub(r"\s+", " ", text).strip()
        print("Final cleaned text:", text) # 🧠 STEP 6: DEBUG PRINT

        logging.debug(f"Parsing (cleaned): '{text}'")

        # MANDATORY SAFEGUARD: FORCE DELETE IF BOTH WORDS PRESENT
        if "delete" in text and "file" in text and not any(w in text for w in ["don't", "do not", "never"]):
            # Reconstruct dummy string
            target_str = text.split("file")[-1].strip()
            if not target_str:
                target_str = "target"
            intent_match = ("DELETE_FILE", target_str) # Pass as tuple
            return self._finalize(intent_match, original_text, extract_file_metadata=True)

        # Priority 2 — File System
        result = self._match_group(self._file_patterns, text)
        if result:
            parsed = self._finalize(result, original_text, extract_file_metadata=True)
            # 5️⃣ FIX OPEN FILE EXPLORER MISCLASSIFICATION
            if parsed["intent"] == "OPEN_FILE" and parsed["target"] in ["explorer", "file explorer"]:
                parsed["intent"] = "OPEN_APP"
                parsed["target"] = "explorer"
            # 8️⃣ FIX OPEN FOLDER GENERIC COMMAND
            if parsed["intent"] == "OPEN_FOLDER" and not parsed["target"]:
                parsed["target"] = "desktop"
                parsed["entity"] = "desktop"
            return parsed

        # Priority 3 — System Control
        result = self._match_group(self._system_patterns, text)
        if result:
            return self._finalize(result, original_text)

        # Priority 4 — Media Control (same SYSTEM_CONTROL intent bucket)
        result = self._match_group(self._media_patterns, text)
        if result:
            return self._finalize(result, original_text)

        # Priority 5 — App Control
        is_app = False
        app_target = text
        if text.startswith("open ") or text.startswith("start ") or text.startswith("launch "):
            is_app = True
            app_target = re.sub(r"^(open|start|launch)\s+", "", text).strip()
        else:
            # Check if it matches a known app (exact or fuzzy)
            if text in self.KNOWN_APPS:
                is_app = True
                app_target = text
            else:
                import difflib
                close_apps = difflib.get_close_matches(text, self.KNOWN_APPS, n=1, cutoff=0.85)
                if close_apps:
                    is_app = True
                    app_target = close_apps[0]

        if is_app:
            return self._finalize(("OPEN_APP", app_target), original_text)

        # 🧠 STEP 4 & 5: PARTIAL MATCH / FALLBACK AI LOGIC
        if "delete" in text:
            target = text.replace("delete", "").replace("file", "").replace(" in ", "").strip()
            return {"intent": "DELETE_FILE", "entity": target, "target": target, "metadata": {}, "original_text": original_text}
        elif "open" in text:
            target = text.replace("open", "").strip()
            return {"intent": "OPEN_APP", "entity": target, "target": target, "metadata": {}, "original_text": original_text}
        elif "create" in text:
            target = text.replace("create", "").replace("file", "").replace(" in ", "").strip()
            return {"intent": "CREATE_FILE", "entity": target, "target": target, "metadata": {}, "original_text": original_text}

        # Unknown
        logging.debug(f"No intent matched for: '{text}'")
        return {"intent": "UNKNOWN", "entity": None, "target": None,
                "metadata": {}, "original_text": original_text}

    # ─────────────────── PRIVATE HELPERS ─────────────────────────────────────

    def _match_group(self, pattern_dict: dict, text: str):
        """Try every pattern in a group dict. Return (intent, match) or None."""
        for intent, patterns in pattern_dict.items():
            for pattern in patterns:
                m = re.search(pattern, text)
                if m:
                    return intent, m
        return None

    def _finalize(self, intent_match, text: str, extract_file_metadata=False) -> dict:
        intent, match = intent_match
        
        logging.info(f"Regex match: {match}")
        logging.info(f"Type: {type(match)}")
        
        metadata = {}
        
        if isinstance(match, str):
            raw_entity = match
        elif match and hasattr(match, 'groupdict') and match.groupdict().get("name"):
            # 🧠 STEP 3 SUPPORT: Handle Named Groups
            raw_entity = match.group("name").strip()
            
            if match.groupdict().get("type"):
                metadata["file_type"] = match.group("type").strip()
            if match.groupdict().get("parent"):
                metadata["parent_folder"] = match.group("parent").strip()
            if match.groupdict().get("destination"):
                metadata["destination"] = match.group("destination").strip()
                
        elif match and hasattr(match, 'groups') and match.groups():
            raw_entity = match.group(1).strip()
        else:
            raw_entity = None

        # Strip leading articles
        if raw_entity:
            raw_entity = re.sub(r"^(the|a|an)\s+", "", raw_entity).strip()

        target = raw_entity

        # ── Normalize SYSTEM_CONTROL entity ──────────────────────────────────
        if intent == "SYSTEM_CONTROL":
            if raw_entity:
                target = self._sys_action_map.get(raw_entity, raw_entity.upper().replace(" ", "_"))
            metadata["action"] = target

        # ── Extract file-type metadata ────────────────────────────────────────
        if extract_file_metadata and "file_type" in metadata:
            ext = self.FILE_TYPE_MAP.get(metadata["file_type"])
            if ext:
                metadata["ext"] = ext

        logging.info(f"Parsed intent: {intent} | target: {target} | metadata: {metadata}")

        return {
            "intent":        intent,
            "entity":        target,   # backwards-compat key still used by ActionManager/Controller
            "target":        target,
            "metadata":      metadata,
            "original_text": text,
        }
