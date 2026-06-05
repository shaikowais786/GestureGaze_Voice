import logging

class SecurityMode:
    def __init__(self):
        self._enabled = True # Default state can be configured
        logging.info("Security Mode initialized (Enabled by default).")

    def enable(self):
        """Enables secure mode."""
        self._enabled = True
        logging.info("Security Mode ENABLED.")

    def disable(self):
        """Disables secure mode."""
        self._enabled = False
        logging.info("Security Mode DISABLED.")

    def is_enabled(self):
        """Returns True if secure mode is active."""
        return self._enabled
