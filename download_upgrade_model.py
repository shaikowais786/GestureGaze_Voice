import os
import shutil
import urllib.request
import zipfile
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Official Vosk model (accurate)
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
MODEL_ZIP_NAME = "vosk-model-en-us-0.22.zip"
EXTRACTED_FOLDER_NAME = "vosk-model-en-us-0.22"
DEST_MODEL_DIR = "models"
CURRENT_MODEL_PATH = os.path.join(DEST_MODEL_DIR, "model")
OLD_MODEL_BACKUP = os.path.join(DEST_MODEL_DIR, "model_small_backup")

def show_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = downloaded * 100 / total_size
        print(f"\rDownloading: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)", end="")
    else:
        print(f"\rDownloading: {downloaded / (1024*1024):.1f} MB", end="")

def download_and_upgrade():
    # Ensure models directory exists
    if not os.path.exists(DEST_MODEL_DIR):
        os.makedirs(DEST_MODEL_DIR)
        
    zip_path = os.path.join(DEST_MODEL_DIR, MODEL_ZIP_NAME)
    
    # 1. Download
    if not os.path.exists(zip_path):
        logging.info(f"Downloading model (approx 1.8GB)... be patient.")
        logging.info(f"URL: {MODEL_URL}")
        try:
            urllib.request.urlretrieve(MODEL_URL, zip_path, reporthook=show_progress)
            print() # Newline after progress
            logging.info("Download complete.")
        except Exception as e:
            logging.error(f"Download failed: {e}")
            return
    else:
        logging.info("Model zip already exists. Skipping download.")

    # 2. Extract
    logging.info("Extracting model...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DEST_MODEL_DIR)
        logging.info("Extraction complete.")
    except Exception as e:
        logging.error(f"Extraction failed: {e}")
        return

    # 3. Swap Models
    extracted_path = os.path.join(DEST_MODEL_DIR, EXTRACTED_FOLDER_NAME)
    
    if os.path.exists(extracted_path):
        # Backup old model if it exists and isn't already backed up
        if os.path.exists(CURRENT_MODEL_PATH):
            if os.path.exists(OLD_MODEL_BACKUP):
                shutil.rmtree(OLD_MODEL_BACKUP)
            
            logging.info(f"Backing up current small model to {OLD_MODEL_BACKUP}...")
            os.rename(CURRENT_MODEL_PATH, OLD_MODEL_BACKUP)
            
        # Move new model to 'model'
        logging.info(f"Installing new model to {CURRENT_MODEL_PATH}...")
        os.rename(extracted_path, CURRENT_MODEL_PATH)
        
        logging.info("Upgrade successful! You can now delete the zip file if you wish.")
        logging.info("Please restart main.py to use the new model.")
        
    else:
        logging.error(f"Extracted folder {extracted_path} not found. Something went wrong.")

if __name__ == "__main__":
    confirm = input("This will download a 1.8GB model to improve speech accuracy. Continue? (y/n): ")
    if confirm.lower() == 'y':
        download_and_upgrade()
    else:
        print("Cancelled.")
