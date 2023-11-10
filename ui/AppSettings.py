from PyQt6 import QtCore
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QApplication

settings = QtCore.QSettings('GeoChron', 'GeoChron2')




# Restore settings if exist or set a default
if settings.contains("theme_selection"):
    # there is the key in QSettings
    print('Checking for theme preference in config')
    theme_selection = settings.value('theme_selection')
    print('Found theme_selection in config:' + theme_selection)
else:
    print('theme_selection not found in config. Using default Darkmode')
    settings.setValue('theme_selection', 'Dark')
    pass

if settings.contains("panel_name"):
    # there is the key in QSettings
    print('Checking for default panel_name in config')
    panel_name = settings.value('panel_name')
    print('Found panel_name in config:' + str(panel_name))
else:
    print('panel_name not found in config. Using default: Cyberpanel')
    settings.setValue('panel_name', 'cyberpanel')
    panel_name = str(settings.value('panel_name'))
    pass



class AppContext():
    def run(self):
        global version, current_version, current_release_notes_url, license_type, trial_license, lite_license, premium_license, professional_license, corporate_license, license_expiration, license_key_is_valid, license_key, license_string, current_release_url
        version = self.build_settings['version']
        QApplication.setApplicationName("WizardAssistantDesktop")
        QApplication.setOrganizationName("WizardAssistant")
        QApplication.setOrganizationDomain("wizardassistant.com")
        # Splash startup screen initialization
        self.splash = QSplashScreen(
            QPixmap(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'images', 'chevron_logo.png')))
        self.splash.show()
        self.settings = QSettings()
        print(self.settings.fileName())

        def load_license_from_config():
            global license_string
            if self.settings.contains("license"):
                # there is the key in QSettings
                print('Checking for license in config')
                license_string = self.settings.value('license')
                print('Found license in config:' + license_string)
            else:
                print('License not found in config')
                pass