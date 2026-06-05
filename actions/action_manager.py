import logging
from .system_controller import SystemController
from .app_controller import AppController
from .file_controller import FileController

class ActionManager:
    def __init__(self, security_mode_manager):
        self.system_controller = SystemController()
        self.app_controller = AppController()
        self.file_controller = FileController()
        self.security_mode = security_mode_manager
        
        # Actions that require explicit user confirmation
        self.dangerous_actions = ["LOCK_SYSTEM"]

    def _get_requested_exts(self, metadata, entity):
        TYPE_TO_EXTS = {
            "word": (".docx", ".doc"),
            "excel": (".xlsx", ".xls", ".csv"),
            "powerpoint": (".pptx", ".ppt"),
            "power": (".pptx", ".ppt"),
            "pp": (".pptx", ".ppt"),
            "text": (".txt",),
            "python": (".py",),
            "html": (".html", ".htm"),
            "image": (".png", ".jpg", ".jpeg", ".gif"),
            "pdf": (".pdf",),
            "zip": (".zip",),
            "zi": (".zip",)
        }
        
        file_type = metadata.get("file_type")
        if not file_type and entity and " in " in entity:
            file_type = entity.rsplit(" in ", 1)[1].strip()
            
        if file_type:
            return TYPE_TO_EXTS.get(file_type.lower())
            
        ext = metadata.get("ext")
        if ext:
            return (ext,)
            
        return None

    def handle(self, intent, target, metadata):
        """Wrapper handle explicitly requested by state controller."""
        if metadata is None:
            metadata = {}
        metadata["confirmed"] = True
        return self.handle_command({"intent": intent, "target": target, "entity": target, "metadata": metadata})

    def handle_command(self, parsed_command):
        """
        Central dispatcher for commands.
        Returns a result dict that might indicate a need for confirmation.
        """
        intent = parsed_command.get("intent")
        entity = parsed_command.get("target") or parsed_command.get("entity") # fallback
        metadata = parsed_command.get("metadata", {})
        
        logging.info(f"ActionManager handling: {intent} -> {entity} | metadata: {metadata}")

        if intent == "SYSTEM_CONTROL":
            if entity in self.dangerous_actions and not metadata.get("confirmed"):
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "pending_action": {
                        "intent": intent,
                        "target": entity,
                        "metadata": metadata
                    },
                    "message": f"Are you sure you want to {entity.replace('_', ' ').lower()}?"
                }
            
            success = self.system_controller.execute(entity)
            if success:
                if entity == "VOLUME_UP": msg = "Volume increased"
                elif entity == "VOLUME_DOWN": msg = "Volume decreased"
                elif entity == "MUTE": msg = "System muted"
                elif entity == "UNMUTE": msg = "System unmuted"
                elif entity == "BRIGHTNESS_UP": msg = "Brightness increased"
                elif entity == "BRIGHTNESS_DOWN": msg = "Brightness decreased"
                elif entity == "SCREENSHOT": msg = "Screenshot taken"
                elif entity == "MINIMIZE_WINDOW": msg = "Window minimized"
                elif entity == "CLOSE_WINDOW": msg = "Window closed"
                elif entity == "PLAY": msg = "Playing media"
                elif entity == "PAUSE": msg = "Paused"
                elif entity == "NEXT": msg = "Next track"
                elif entity == "PREVIOUS": msg = "Previous track"
                else: msg = "Done"
            else:
                msg = "Action failed"
                
            return {
                "success": success,
                "requires_confirmation": False, 
                "message": msg
            }

        elif intent == "OPEN_APP":
            success, msg, app_key = self.app_controller.launch_app(entity)
            if success:
                return {
                    "success": True,
                    "requires_confirmation": False,
                    "message": msg
                }
            else:
                # SMART BEHAVIOR: Fallback to file/folder system mapping only if an explicit verb was used
                orig_text = parsed_command.get("original_text", "").lower()
                has_verb = any(v in orig_text for v in ["open", "start", "launch", "run", "go to"])
                if has_verb:
                    item_path, item_type = self.file_controller.search_item(entity)
                    if item_path:
                        self.file_controller.open_item(item_path)
                        return {
                            "success": True,
                            "requires_confirmation": False,
                            "message": f"Opening {item_type}"
                        }
                return {
                    "success": False,
                    "requires_confirmation": False,
                    "message": msg or f"Could not find application or item {entity}"
                }

        elif intent == "OPEN_FOLDER":
             folder, _ = self.file_controller.find_file(entity)
             if folder and folder["type"] == "folder":
                 import os
                 os.startfile(folder["path"])
                 return {"success": True, "requires_confirmation": False, "message": "Opening folder"}
             else:
                 return {"success": False, "requires_confirmation": False, "message": "Folder not found"}

        elif intent == "SEARCH_FILE":
             file_name = entity
             if entity and " in " in entity:
                  file_name = entity.rsplit(" in ", 1)[0].strip()
             
             # Use find_items with file-only filter to avoid matching folders
             results = self.file_controller.find_items(file_name, item_type="file")
             
             # Filter by extension if requested
             req_exts = self._get_requested_exts(metadata, entity)
             if req_exts:
                 results = [r for r in results if any(r["name"].endswith(ext) for ext in req_exts)]

             if not results:
                 return {"success": False, "requires_confirmation": False, "message": "File not found"}
             
             # Show up to 5 matching files with their full names
             file_names = [item["name"] for item in results[:5]]
             print("Search results:", file_names)
             
             if len(file_names) == 1:
                 return {"success": True, "requires_confirmation": False, "message": f"I found {file_names[0]}"}
             else:
                 names_str = ", ".join(file_names[:3])
                 return {"success": True, "requires_confirmation": False, "message": f"I found {len(file_names)} files: {names_str}"}

        elif intent == "CREATE_FILE":
             ext_word = metadata.get("file_type")
             
             if not ext_word and entity and " in " in entity:
                 parts = entity.rsplit(" in ", 1)
                 entity = parts[0].strip()
                 ext_word = parts[1].strip()
                 
             if not ext_word:
                 return {"success": False, "requires_confirmation": False, "message": "Please specify file type"}
                 
             success, msg = self.file_controller.create_file(entity, ext_word)
             return {"success": success, "requires_confirmation": False, "message": msg}

        elif intent == "CREATE_FOLDER":
             import os
             folder_path = os.path.join(self.file_controller.desktop_path, entity)
             if not os.path.exists(folder_path):
                 os.makedirs(folder_path)
                 self.file_controller.refresh_cache()
                 return {"success": True, "requires_confirmation": False, "message": "Folder created"}
             else:
                 return {"success": False, "requires_confirmation": False, "message": "Folder already exists"}

        elif intent == "DELETE_FILE":
             import os
             from send2trash import send2trash
             file_name = entity
             
             req_exts = self._get_requested_exts(metadata, entity)
             
             if entity and " in " in entity:
                  file_name = entity.rsplit(" in ", 1)[0].strip()
                  
             results = self.file_controller.find_items(file_name, item_type="file")
             
             if req_exts:
                  results = [r for r in results if any(r["name"].endswith(ext) for ext in req_exts)]
                  
             if not results:
                 return {"success": False, "requires_confirmation": False, "message": "File not found"}
                 
             file_item = results[0]

             # 🔥 INSTANT DELETE — move to Recycle Bin (safe, no confirmation)
             try:
                 send2trash(file_item["path"])
                 self.file_controller.refresh_cache()
                 logging.info(f"File sent to Recycle Bin: {file_item['path']}")
                 return {"success": True, "requires_confirmation": False, "message": "File deleted"}
             except Exception as e:
                 logging.error(f"Failed to delete file: {e}")
                 return {"success": False, "requires_confirmation": False, "message": "Error deleting file"}

        elif intent == "MOVE_FILE":
             file_name = entity
             if entity and " to " in entity:
                  parts = entity.rsplit(" to ", 1)
                  file_name = parts[0].strip()
                  dest_folder_name = parts[1].strip()
             else:
                  dest_folder_name = metadata.get("destination") or entity # fallback

             if " in " in file_name:
                  file_name = file_name.rsplit(" in ", 1)[0].strip()

             results = self.file_controller.find_items(file_name, item_type="file")
             if not results:
                 return {"success": False, "requires_confirmation": False, "message": "File not found"}
                 
             file_path = results[0]["path"]
             success, msg = self.file_controller.move_file(file_path, dest_folder_name)
             return {"success": success, "requires_confirmation": False, "message": msg}

        elif intent == "OPEN_FILE":
             import os
             file_name = entity
             
             req_exts = self._get_requested_exts(metadata, entity)
             
             if entity and " in " in entity:
                  file_name = entity.rsplit(" in ", 1)[0].strip()

             # Handle "inside [folder]" — search within a specific parent folder
             parent_folder = metadata.get("parent_folder")
             if parent_folder:
                  # Find the parent folder first
                  folder_item, _ = self.file_controller.find_file(parent_folder)
                  if folder_item and folder_item["type"] == "folder":
                       # Search for the file inside that folder
                       for item in self.file_controller.cached_items:
                            if item["type"] == "file" and os.path.dirname(item["path"]) == folder_item["path"]:
                                 item_base = os.path.splitext(item["name"])[0]
                                 if item_base == file_name.lower() or file_name.lower() in item_base:
                                      os.startfile(item["path"])
                                      return {"success": True, "requires_confirmation": False, "message": f"Opening {item['name']}"}
                       return {"success": False, "requires_confirmation": False, "message": f"File not found in {parent_folder}"}

             results = self.file_controller.find_items(file_name, item_type="file")
             
             if req_exts:
                  results = [r for r in results if any(r["name"].endswith(ext) for ext in req_exts)]
                  
             if not results:
                 return {"success": False, "requires_confirmation": False, "message": "File not found"}
                 
             file_item = results[0]
                 
             os.startfile(file_item["path"])
             return {"success": True, "requires_confirmation": False, "message": f"Opening {file_item['name']}"}

        elif intent == "OPEN_FOLDER":
             if entity == "desktop":
                 import subprocess
                 subprocess.Popen(f'explorer "{self.file_controller.desktop_path}"', shell=True)
                 return {"success": True, "requires_confirmation": False, "message": "Opening Desktop"}
                 
             folder, _ = self.file_controller.find_file(entity)
             if folder and folder["type"] == "folder":
                 import os
                 os.startfile(folder["path"])
                 return {"success": True, "requires_confirmation": False, "message": "Opening folder"}
             else:
                 return {"success": False, "requires_confirmation": False, "message": "Folder not found"}

        elif intent == "OPEN_IN_VSCODE":
             import subprocess
             file_name = entity
             if entity and " in " in entity:
                  file_name = entity.rsplit(" in ", 1)[0].strip()
                  
             file_item, _ = self.file_controller.find_file(file_name)
             if not file_item:
                 return {"success": False, "requires_confirmation": False, "message": "File not found"}
                 
             subprocess.Popen(f'code "{file_item["path"]}"', shell=True)
             return {"success": True, "requires_confirmation": False, "message": "Opening in VS Code"}

        elif intent == "TAKE_SCREENSHOT":
            file_path = self.system_controller.take_screenshot()
            return {
                "success": bool(file_path),
                "requires_confirmation": False,
                "message": "Screenshot saved." if file_path else "Failed to take screenshot."
            }

        elif intent == "SECURE_MODE":
            self.security_mode.enable()
            return {
                "success": True, 
                "requires_confirmation": False, 
                "message": "Secure voice mode enabled"
            }
            
        elif intent == "VOICE_MODE":
            # Handled by Controller state machine usually, but good to have here
            return {"success": True, "message": "Voice mode is active"}

        elif intent == "UNKNOWN":
            return {"success": False, "message": "Command not recognized"}

        return {"success": False, "message": "No handler for this intent"}
