import os
import pickle
import logging

class UserManager:
    def __init__(self, profiles_path="users/voice_profiles.pkl"):
        self.profiles_path = profiles_path
        self.profiles = self._load_profiles()

    def _load_profiles(self):
        """Loads voice profiles from the pickle file."""
        if not os.path.exists(self.profiles_path):
            logging.info("No existing voice profiles found. Starting fresh.")
            return {}
        
        try:
            with open(self.profiles_path, "rb") as f:
                profiles = pickle.load(f)
                logging.info(f"Loaded {len(profiles)} voice profiles.")
                return profiles
        except (EOFError, pickle.UnpicklingError):
            logging.warning("Corrupt or empty profiles file. Resetting.")
            return {}
        except Exception as e:
            logging.error(f"Error loading profiles: {e}")
            return {}

    def _save_profiles(self):
        """Saves current profiles to the pickle file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.profiles_path), exist_ok=True)
        try:
            with open(self.profiles_path, "wb") as f:
                pickle.dump(self.profiles, f)
            logging.info("Voice profiles saved successfully.")
        except Exception as e:
            logging.error(f"Error saving profiles: {e}")

    def register_user(self, username, embedding):
        """Registers a new user with their voice embedding."""
        if username in self.profiles:
            logging.warning(f"User '{username}' already exists. Overwriting.")
        
        self.profiles[username] = embedding
        self._save_profiles()
        logging.info(f"User '{username}' registered.")

    def get_embedding(self, username):
        """Returns the embedding for a specific user."""
        return self.profiles.get(username)

    def get_all_profiles(self):
        """Returns all registered profiles."""
        return self.profiles

    def user_exists(self, username):
        """Checks if a user is registered."""
        return username in self.profiles

    def delete_user(self, username):
        """Deletes a specific user's voice profile."""
        if username in self.profiles:
            del self.profiles[username]
            self._save_profiles()
            logging.info(f"User '{username}' deleted.")
            return True
        return False

    def clear_all_users(self):
        """Clears all voice profiles."""
        self.profiles.clear()
        self._save_profiles()
        logging.info("All voice profiles cleared.")
