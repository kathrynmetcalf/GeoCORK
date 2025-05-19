from PyQt6.QtCore import QSettings


class SettingsManager:
    """
    Singleton class to manage application settings.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._settings = QSettings('GeoCORK', 'GeoCORK')
            cls._instance._db_settings = None
        return cls._instance

    def __getattr__(self, name):
        return getattr(self.settings, name)

    @property
    def settings(self):
        return self._settings

    @property
    def db_settings(self):
        return self._db_settings

    def set_db_file(self, db_file: str):
        # Settings specific to each database file
        self._db_settings = QSettings('GeoCORK', f'GeoCORK : {db_file}')
