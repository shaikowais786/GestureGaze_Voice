import os
import logging
import subprocess
from difflib import get_close_matches

class FileController:
    def __init__(self, desktop_path=None):
        if desktop_path:
            self.desktop_path = desktop_path
        else:
            user_home = os.path.expanduser("~")
            self.desktop_path = os.path.join(user_home, "OneDrive", "Desktop")
            
            if not os.path.exists(self.desktop_path):
                self.desktop_path = os.path.join(user_home, "Desktop")
            
        self.cached_items = []
        self.refresh_cache()

    def refresh_cache(self):
        logging.info("Refreshing item cache from Desktop...")
        try:
            from win32com.shell import shell, shellcon
            shell.SHChangeNotify(shellcon.SHCNE_ALLEVENTS, shellcon.SHCNF_IDLIST, None, None)
        except Exception:
            pass

        self.cached_items.clear()
        
        if not os.path.exists(self.desktop_path):
             return
        
        max_depth = 2  # Desktop level + 1 subfolder level
        desktop_depth = self.desktop_path.rstrip(os.sep).count(os.sep)
             
        for root, dirs, files in os.walk(self.desktop_path):
             current_depth = root.rstrip(os.sep).count(os.sep) - desktop_depth
             
             # Skip hidden directories and limit depth
             dirs[:] = [d for d in dirs if not d.startswith('.') and current_depth < max_depth]
             
             for d in dirs:
                  full_path = os.path.join(root, d)
                  self.cached_items.append({
                      "name": d.lower(),
                      "path": full_path,
                      "type": "folder"
                  })
             
             for f in files:
                  if f.startswith('.'):
                      continue
                  full_path = os.path.join(root, f)
                  self.cached_items.append({
                      "name": f.lower(),
                      "path": full_path,
                      "type": "file"
                  })
             
        logging.info(f"Cached {len(self.cached_items)} items")

    def find_file(self, query):
        if not query or not query.strip():
            return None, []
        # Strip extensions before comparing to heavily boost fuzzy score
        names_cleaned = [os.path.splitext(item["name"])[0] for item in self.cached_items]
        matches = get_close_matches(query.lower(), names_cleaned, n=3, cutoff=0.70)
        
        if not matches:
            return None, []
            
        best = matches[0]
        
        for item in self.cached_items:
            if os.path.splitext(item["name"])[0] == best:
                return item, matches
                
        return None, []

    def find_items(self, query, item_type=None, parent_folder_path=None):
        """
        Searches for items and returns up to 3 best matches.
        """
        if not query or not query.strip():
            return []
        target_name = query.lower()
        pool = self.cached_items
        
        if item_type:
            pool = [i for i in pool if i["type"] == item_type]
        if parent_folder_path:
            pool = [i for i in pool if i["path"].startswith(parent_folder_path)]
        
        # 1. Exact match
        exact = [i for i in pool if i["name"] == target_name]
        if exact:
            return exact
            
        # 2. Keyword Filter (High Priority)
        filtered = [i for i in pool if target_name in i["name"]]
        if filtered:
            # Sort by directory depth first (prioritize root Desktop over subfolders), then by name length
            filtered.sort(key=lambda x: (x["path"].count(os.sep), len(x["name"])))
            return filtered
            
        # 3. Fuzzy fallback
        pool_names_cleaned = [os.path.splitext(i["name"])[0].lower() for i in pool]
        matches = get_close_matches(target_name, pool_names_cleaned, n=10, cutoff=0.60)
        
        if matches:
            res = []
            for m in matches:
                for i in pool:
                    if os.path.splitext(i["name"])[0].lower() == m and i not in res:
                        res.append(i)
            return res

        return []

    def search_item(self, query, item_type=None, parent_folder_path=None):
        if not query or not query.strip():
            return None, None
        items = self.find_items(query, item_type, parent_folder_path)
        if items:
            best = items[0]
            logging.info(f"Best match ({best['type']}): {os.path.basename(best['path'])}")
            return best['path'], best['type']
        return None, None

    def open_item(self, path):
        """
        Opens a folder or file natively, using VSCode for Python scripts.
        """
        if not path or not os.path.exists(path):
            return False
            
        try:
            print(f"Resolved path: {path}")
            if os.path.isdir(path):
                subprocess.Popen(f'explorer "{path}"', shell=True)
            elif os.path.isfile(path) and path.lower().endswith(".py"):
                subprocess.Popen(f'code "{path}"', shell=True)
            else:
                os.startfile(path)
            return True
        except Exception as e:
            logging.error(f"Error opening item {path}: {e}")
            return False

    def open_in_vscode(self, path):
        if not path or not os.path.exists(path):
            return False
        try:
            print(f"Resolved path: {path}")
            subprocess.Popen(f'code "{path}"', shell=True)
            return True
        except Exception:
            return False

    # Backwards compatibility wrappers
    def find_files(self, filename):
        return [i["path"] for i in self.find_items(filename, item_type="file")]

    def search_file(self, filename):
        path, _ = self.search_item(filename, item_type="file")
        return path

    def open_file(self, file_path):
        return self.open_item(file_path)

    # ---------------- CRUD File Methods ----------------
    def create_folder(self, folder_name):
        folder_path = os.path.join(self.desktop_path, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            self.refresh_cache()
            return True, "Folder created"
        return False, "Folder already exists"

    def create_file(self, file_name, file_type):
        file_types = {
            "word": ".docx",
            "excel": ".xlsx",
            "text": ".txt",
            "powerpoint": ".pptx",
            "power": ".pptx",
            "pp": ".pptx",
            "image": ".png",
            "zip": ".zip",
            "python": ".py",
            "html": ".html",
            "pdf": ".pdf"
        }
        ext = file_types.get(file_type.lower())
        if not ext:
            return False, "Unsupported file type"
            
        file_path = os.path.join(self.desktop_path, file_name + ext)
        if os.path.exists(file_path):
            return False, "File already exists"
            
        try:
            # Create proper Office documents (not 0-byte files)
            if ext == ".docx":
                try:
                    from docx import Document
                    doc = Document()
                    doc.save(file_path)
                except ImportError:
                    self._create_minimal_office_file(file_path, ext)
            elif ext == ".xlsx":
                try:
                    from openpyxl import Workbook
                    wb = Workbook()
                    wb.save(file_path)
                except ImportError:
                    self._create_minimal_office_file(file_path, ext)
            elif ext == ".pptx":
                try:
                    from pptx import Presentation
                    prs = Presentation()
                    prs.save(file_path)
                except ImportError:
                    self._create_minimal_office_file(file_path, ext)
            else:
                # Plain text, python, etc. — empty file is fine
                open(file_path, 'w').close()
                
            self.refresh_cache()
            return True, f"{file_type} file created"
        except Exception as e:
            logging.error(f"Error creating file: {e}")
            return False, "Error creating file"

    def _create_minimal_office_file(self, file_path, ext):
        """Create a minimal valid Office file using ZIP structure as fallback."""
        import zipfile
        import io
        
        if ext == ".xlsx":
            # Minimal valid xlsx (ZIP with required XML parts)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
                zf.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
                zf.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
                zf.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
                zf.writestr('xl/worksheets/sheet1.xml', '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>')
            with open(file_path, 'wb') as f:
                f.write(buf.getvalue())
        elif ext == ".docx":
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
                zf.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
                zf.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t></w:t></w:r></w:p></w:body></w:document>')
            with open(file_path, 'wb') as f:
                f.write(buf.getvalue())
        elif ext == ".pptx":
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/></Types>')
                zf.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
                zf.writestr('ppt/presentation.xml', '<?xml version="1.0" encoding="UTF-8"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldMasterIdLst/><p:sldIdLst/><p:sldSz cx="9144000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
            with open(file_path, 'wb') as f:
                f.write(buf.getvalue())

    def delete_file(self, file_path):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.refresh_cache()
                return True
            except Exception as e:
                logging.error(f"Error deleting file: {e}")
                return False
        return False

    def move_file(self, file_path, folder_name):
        import shutil
        dest_folder, _ = self.search_item(folder_name, item_type="folder")
        if dest_folder and os.path.exists(dest_folder):
            try:
                shutil.move(file_path, dest_folder)
                self.refresh_cache()
                return True, "File moved"
            except Exception as e:
                logging.error(f"Error moving file: {e}")
                return False, "Error moving file"
        return False, "Destination folder not found"
