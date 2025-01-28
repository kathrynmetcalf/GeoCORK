from PyQt6.QtCore import QSettings

class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.settings = QSettings()
        return cls._instance

    def __getattr__(self, name):
        return getattr(self.settings, name)

    # def init_settings(self):
    #     self.settings = QSettings()



settings = SettingsManager()