"""
sesar_settings_tab.py
---------------------
"SESAR" tab for GeoCORK's SettingsDialog (Settings.py).

Built in code rather than in Settings.ui so the .ui file doesn't need to
change. Settings.py adds it with:

    self.sesar_tab = SesarSettingsTab(self)
    self.settings_tabWidget.addTab(self.sesar_tab, "SESAR")

and calls ``self.sesar_tab.save()`` from ``update_settings()``.

What it stores
    sesar_environment          QSettings  ("sandbox" | "production")
    sesar_code                 QSettings  (your SESAR user/lab code, needed to publish)
    sesar_default_object_type  QSettings  (pre-fills object_type when registering)
    access / refresh tokens    OS keyring per environment (QSettings fallback)

Restore Defaults in the Settings dialog deliberately does NOT touch these —
wiping someone's tokens because they reset font sizes would be unkind.
"""

from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QApplication, QComboBox, QFormLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QToolButton, QVBoxLayout, QWidget)

from Sesar_Import import sesar_api_client as api


_ENV_LABELS = {"sandbox": "Sandbox (testing — IGSNs not official)",
               "production": "Production (official IGSNs)"}


class _SecretEdit(QWidget):
    """Password-style line edit with a show/hide toggle."""

    def __init__(self, placeholder: str, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit.setPlaceholderText(placeholder)
        self.toggle = QToolButton()
        self.toggle.setText("Show")
        self.toggle.setCheckable(True)
        self.toggle.toggled.connect(self._on_toggle)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.toggle)

    def _on_toggle(self, shown: bool):
        self.edit.setEchoMode(QLineEdit.EchoMode.Normal if shown
                              else QLineEdit.EchoMode.Password)
        self.toggle.setText("Hide" if shown else "Show")

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, value: Optional[str]):
        self.edit.setText(value or "")


class SesarSettingsTab(QWidget):
    def __init__(self, parent=None, settings=None, token_store=None):
        super().__init__(parent)
        self._settings = settings if settings is not None else api._get_qsettings()
        self._store = token_store if token_store is not None else api.TokenStore(self._settings)
        # Unsaved token edits per environment, so flipping the environment
        # combo back and forth doesn't lose what the user pasted.
        self._pending: Dict[str, Dict[str, str]] = {}
        self._loaded_env: Optional[str] = None
        self._build_ui()
        self.load()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = QVBoxLayout(self)

        env_box = QGroupBox("Connection")
        env_form = QFormLayout(env_box)
        self.env_combo = QComboBox()
        for key in api.ENVIRONMENTS:
            self.env_combo.addItem(_ENV_LABELS.get(key, key), key)
        self.env_combo.currentIndexChanged.connect(self._on_env_changed)
        env_form.addRow("Environment:", self.env_combo)
        self.base_url_label = QLabel()
        self.base_url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        env_form.addRow("API endpoint:", self.base_url_label)
        self.sesar_code_edit = QLineEdit()
        self.sesar_code_edit.setPlaceholderText("e.g. IEABC — required to publish new samples")
        env_form.addRow("SESAR code:", self.sesar_code_edit)
        self.object_type_edit = QLineEdit()
        self.object_type_edit.setPlaceholderText(api.DEFAULT_OBJECT_TYPE)
        self.object_type_edit.setToolTip(
            "Default SESAR object type (leaf label) used when registering new samples. "
            "Can be changed per sample before sending.")
        env_form.addRow("Default object type:", self.object_type_edit)
        root.addWidget(env_box)

        tok_box = QGroupBox("JSON Web Tokens (JWT)")
        tok_form = QFormLayout(tok_box)
        self.access_edit = _SecretEdit("Access token (valid 1 day)")
        self.refresh_edit = _SecretEdit("Refresh token (valid 1 year, rotates on use)")
        tok_form.addRow("Access token:", self.access_edit)
        tok_form.addRow("Refresh token:", self.refresh_edit)
        self.access_status = QLabel()
        self.refresh_status = QLabel()
        tok_form.addRow("Access status:", self.access_status)
        tok_form.addRow("Refresh status:", self.refresh_status)
        self.access_edit.edit.textChanged.connect(self._update_status)
        self.refresh_edit.edit.textChanged.connect(self._update_status)
        self.storage_label = QLabel()
        self.storage_label.setWordWrap(True)
        tok_form.addRow("Stored in:", self.storage_label)

        help_label = QLabel(
            "Generate a token pair in SESAR → user menu → <b>Developer Settings</b> → "
            "<i>Generate New Token</i> (both are shown only once). GeoCORK refreshes "
            "the access token automatically and saves the rotated pair. Reading "
            "published samples does not need a token; updating, registering, and "
            "searching your own samples do.")
        help_label.setWordWrap(True)
        tok_form.addRow(help_label)

        btns = QHBoxLayout()
        self.open_dev_btn = QPushButton("Open Developer Settings…")
        self.open_dev_btn.clicked.connect(self._open_developer_settings)
        self.test_btn = QPushButton("Save && Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        self.clear_btn = QPushButton("Clear Tokens")
        self.clear_btn.clicked.connect(self._clear_tokens)
        btns.addWidget(self.open_dev_btn)
        btns.addStretch()
        btns.addWidget(self.clear_btn)
        btns.addWidget(self.test_btn)
        tok_form.addRow(btns)
        root.addWidget(tok_box)
        root.addStretch()

    # ------------------------------------------------------------ helpers
    def _env(self) -> str:
        return self.env_combo.currentData() or api.DEFAULT_ENVIRONMENT

    def _stash_current_tokens(self):
        if self._loaded_env:
            self._pending[self._loaded_env] = {"access": self.access_edit.text(),
                                               "refresh": self.refresh_edit.text()}

    def _show_tokens_for(self, env: str):
        pending = self._pending.get(env)
        if pending is not None:
            access, refresh = pending["access"], pending["refresh"]
        else:
            access, refresh = self._store.get(env, "access"), self._store.get(env, "refresh")
        self.access_edit.setText(access)
        self.refresh_edit.setText(refresh)
        self._loaded_env = env
        self.base_url_label.setText(api.ENVIRONMENTS[env])
        self._update_status()

    def _update_status(self):
        self.access_status.setText(api.describe_token(self.access_edit.text()))
        self.refresh_status.setText(api.describe_token(self.refresh_edit.text()))
        self.storage_label.setText(self._store.backend_name)

    # ------------------------------------------------------------- slots
    def _on_env_changed(self, _index: int):
        self._stash_current_tokens()
        self._show_tokens_for(self._env())

    def _open_developer_settings(self):
        QDesktopServices.openUrl(QUrl(api.DEVELOPER_SETTINGS_URLS[self._env()]))

    def _clear_tokens(self):
        env = self._env()
        if QMessageBox.question(
                self, "Clear SESAR tokens",
                f"Remove the stored {env} access and refresh tokens from this computer?\n\n"
                "(This does not revoke them on SESAR — use Developer Settings for that.)"
        ) != QMessageBox.StandardButton.Yes:
            return
        self._store.clear(env)
        self._pending.pop(env, None)
        self._show_tokens_for(env)

    def _test_connection(self):
        # Save first: if the test triggers a refresh, SESAR revokes the old
        # refresh token immediately, so the rotated pair MUST be persisted.
        self.save()
        client = api.SesarApiClient(environment=self._env(), token_store=self._store)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            me = client.whoami()
        except api.SesarApiError as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "SESAR connection failed", exc.details())
            self._show_tokens_for(self._env())
            return
        QApplication.restoreOverrideCursor()
        self._pending.pop(self._env(), None)
        self._show_tokens_for(self._env())  # reflect any rotated tokens
        who = (me.get("email") or me.get("username")
               or " ".join(filter(None, [me.get("first_name"), me.get("last_name")]))
               or "your account")
        QMessageBox.information(self, "SESAR connection OK",
                                f"Connected to SESAR {self._env()} as {who}.")

    # -------------------------------------------------------- load/save
    def load(self):
        env = api.current_environment(self._settings)
        idx = self.env_combo.findData(env)
        self.env_combo.blockSignals(True)
        self.env_combo.setCurrentIndex(max(idx, 0))
        self.env_combo.blockSignals(False)
        self.sesar_code_edit.setText(api.configured_sesar_code(self._settings))
        stored_type = self._settings.value(api.SETTING_DEFAULT_OBJECT_TYPE, "")
        self.object_type_edit.setText(str(stored_type or ""))
        self._pending.clear()
        self._show_tokens_for(self._env())

    def save(self):
        self._stash_current_tokens()
        self._settings.setValue(api.SETTING_ENVIRONMENT, self._env())
        self._settings.setValue(api.SETTING_SESAR_CODE, self.sesar_code_edit.text().strip())
        self._settings.setValue(api.SETTING_DEFAULT_OBJECT_TYPE,
                                self.object_type_edit.text().strip() or api.DEFAULT_OBJECT_TYPE)
        for env, toks in self._pending.items():
            for kind in api.TOKEN_KINDS:
                new = (toks.get(kind) or "").strip()
                if new != (self._store.get(env, kind) or ""):
                    self._store.set(env, kind, new)
        self._pending.clear()
        self._update_status()
