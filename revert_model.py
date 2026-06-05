import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEST_MODEL_DIR = "models"
CURRENT_MODEL_PATH = os.path.join(DEST_MODEL_DIR, "model")
OLD_MODEL_BACKUP = os.path.join(DEST_MODEL_DIR, "model_small_backup")

def revert_model():
    if not os.path.exists(OLD_MODEL_BACKUP):
        logging.error(f"Backup folder {OLD_MODEL_BACKUP} not found. Cannot revert.")
        return

    # 1. Remove broken model
    if os.path.exists(CURRENT_MODEL_PATH):
        logging.info("Removing the large model (this might take a few seconds)...")
        shutil.rmtree(CURRENT_MODEL_PATH)

    # 2. Restore small model
    logging.info(f"Restoring backup from {OLD_MODEL_BACKUP}...")
    os.rename(OLD_MODEL_BACKUP, CURRENT_MODEL_PATH)
    
    logging.info("Revert successful! The original small model is back.")
    logging.info("Please restart main.py.")

if __name__ == "__main__":
    confirm = input("This will restore the original small vocabulary model. Continue? (y/n): ")
    if confirm.lower() == 'y':
        revert_model()
    else:
        print("Cancelled.")
