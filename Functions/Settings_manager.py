from PyQt6.QtCore import QSettings


class SettingsManager:
    """
    Singleton class to manage application settings.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.settings = QSettings('GeoCORK', 'GeoCORK')
        return cls._instance

    def __getattr__(self, name):
        return getattr(self.settings, name)


settings = SettingsManager()
