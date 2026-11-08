"""
SesarExportWindow.py
--------------------
Send GeoCORK samples to SESAR.

    • Samples that already have an IGSN  → Update  (PATCH samples/{igsn}/)
      Only fields that differ from SESAR's current record are pre-checked.
    • Samples without an IGSN            → Register (POST samples/)
      SESAR mints the IGSN, which is written back to Samples.SampleIGSN.

Flow
    1. Pick samples on the left (or pass sample_ids= to preselect).
    2. "Prepare" reads each sample from the open database (GUI thread — Qt SQL
       connections are thread-bound) and, for updates, fetches the current
       SESAR record in a background thread to compute the diff.
    3. Review the tree: one node per sample, one child per SESAR field.
       Edit the "GeoCORK value" column, untick fields or whole samples.
       Derived fields (country/province from Regions, material_types from
       RockTypes, sampling_method) start unticked — tick them deliberately.
    4. "Send to SESAR" posts sequentially in a worker thread. Results are
       shown per sample; minted IGSNs are saved to GeoCORK under a savepoint.

Open from code:
    from ui.SesarExportWindow import SesarExportWindow
    SesarExportWindow(sample_ids=[12, 15], parent=main_window).exec()
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (QAbstractItemView, QCheckBox, QDialog, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMessageBox, QPushButton, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

_GEOCORK_ROOT = Path(__file__).resolve().parent.parent
if str(_GEOCORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_GEOCORK_ROOT))

from Sesar_Import import sesar_api_client as api
from Sesar_Import import geocork_exporter as gx
from Sesar_Import.sesar_logger import get_sesar_logger

_ROLE_SAMPLE = Qt.ItemDataRole.UserRole          # on sample nodes: SampleID
_ROLE_FIELD = Qt.ItemDataRole.UserRole + 1       # on field nodes: ExportField
_COL_FIELD, _COL_VALUE, _COL_REMOTE, _COL_NOTE = range(4)

_GREY = QBrush(QColor(140, 140, 140))
_OK = QBrush(QColor(46, 125, 50))
_ERR = QBrush(QColor(198, 40, 40))


# ===========================================================================
# Workers
# ===========================================================================

class RemoteFetchWorker(QThread):
    """GET samples/{igsn}/ for each sample being updated."""
    done = pyqtSignal(dict, dict)   # {sample_id: remote_dict}, {sample_id: error_text}

    def __init__(self, client: api.SesarApiClient, targets: List[Tuple[int, str]], parent=None):
        super().__init__(parent)
        self._client, self._targets = client, targets

    def run(self):
        remotes, errors = {}, {}
        for sample_id, igsn in self._targets:
            try:
                remotes[sample_id] = self._client.get_sample(igsn)
            except api.SesarApiError as exc:
                errors[sample_id] = exc.details()
            except Exception as exc:
                errors[sample_id] = str(exc)
        self.done.emit(remotes, errors)


class SendWorker(QThread):
    """Sequential PATCH/POST; emits one result per sample."""
    progress = pyqtSignal(int, int, str)        # index, total, sample name
    result = pyqtSignal(int, bool, str, object)  # sample_id, ok, message, response
    finished_all = pyqtSignal()

    def __init__(self, client: api.SesarApiClient, jobs: List[dict], parent=None):
        super().__init__(parent)
        self._client, self._jobs = client, jobs

    def run(self):
        for i, job in enumerate(self._jobs, start=1):
            self.progress.emit(i, len(self._jobs), job["name"])
            try:
                if job["action"] == "update":
                    resp = self._client.update_sample(job["igsn"], job["payload"])
                    msg = f"Updated {len(job['payload'])} field(s)"
                else:
                    resp = self._client.register_sample(job["payload"])
                    msg = f"Registered as {resp.get('igsn') or '(no IGSN returned)'}"
                self.result.emit(job["sample_id"], True, msg, resp)
            except api.SesarApiError as exc:
                self.result.emit(job["sample_id"], False, exc.details(), None)
            except Exception as exc:
                self.result.emit(job["sample_id"], False, str(exc), None)
        self.finished_all.emit()


# ===========================================================================
# Window
# ===========================================================================

class SesarExportWindow(QDialog):
    def __init__(self, sample_ids: Optional[List[int]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Send GeoCORK Samples to SESAR")
        self.resize(1250, 720)
        self.setModal(True)
        self._preselect = set(sample_ids or [])
        self._records: Dict[int, gx.SampleRecord] = {}
        self._sample_items: Dict[int, QTreeWidgetItem] = {}
        self._worker: Optional[QThread] = None
        self._minted: List[Tuple[int, str]] = []
        self._client = api.SesarApiClient.from_settings()
        get_sesar_logger().info("SesarExportWindow opened")
        self._build_ui()
        self._reload_samples()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = QVBoxLayout(self)

        env = self._client.environment
        token = "token configured" if self._client.has_credentials() else \
            "<b style='color:#c62828'>no token — add one in Settings → SESAR</b>"
        code = api.configured_sesar_code() or "<i>not set</i>"
        banner = QLabel(
            f"Target: <b style='color:{'#b36b00' if env == 'sandbox' else '#2e7d32'}'>"
            f"SESAR {env}</b> ({self._client.base_url}) — {token} — SESAR code: {code}")
        banner.setWordWrap(True)
        root.addWidget(banner)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # -- left: sample picker
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by name or IGSN…")
        self.filter_edit.textChanged.connect(self._reload_samples)
        lv.addWidget(self.filter_edit)
        self.sample_list = QListWidget()
        lv.addWidget(self.sample_list, 1)
        pick_btns = QHBoxLayout()
        b_all = QPushButton("All")
        b_all.clicked.connect(lambda: self._check_list(True))
        b_none = QPushButton("None")
        b_none.clicked.connect(lambda: self._check_list(False))
        self.prepare_btn = QPushButton("Prepare ▶")
        self.prepare_btn.clicked.connect(self._prepare)
        pick_btns.addWidget(b_all)
        pick_btns.addWidget(b_none)
        pick_btns.addStretch()
        pick_btns.addWidget(self.prepare_btn)
        lv.addLayout(pick_btns)
        splitter.addWidget(left)

        # -- right: review tree
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        opts = QHBoxLayout()
        self.draft_check = QCheckBox("Register new samples as drafts (no coordinates required)")
        opts.addWidget(self.draft_check)
        opts.addStretch()
        opts.addWidget(QLabel("Object type for new samples:"))
        self.object_type_edit = QLineEdit(api.configured_default_object_type())
        self.object_type_edit.setMaximumWidth(220)
        opts.addWidget(self.object_type_edit)
        rv.addLayout(opts)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Sample / SESAR field", "Value to send (editable)",
                                   "Current SESAR value", "Notes"])
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                                  | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(_COL_FIELD, 260)
        self.tree.setColumnWidth(_COL_VALUE, 280)
        self.tree.setColumnWidth(_COL_REMOTE, 240)
        self.tree.itemChanged.connect(self._on_tree_item_changed)
        rv.addWidget(self.tree, 1)

        hint = QLabel("Tick the fields to send. Grey notes explain where a value came from. "
                      "Lists (material types, other names) replace SESAR's whole list. "
                      "Latitude/longitude can't be cleared once set on SESAR.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray")
        rv.addWidget(hint)
        splitter.addWidget(right)
        splitter.setSizes([300, 950])
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        self.status_label = QLabel("Select samples and click Prepare.")
        self.send_btn = QPushButton("Send to SESAR")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._send)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        bottom.addWidget(self.status_label, 1)
        bottom.addWidget(self.send_btn)
        bottom.addWidget(close_btn)
        root.addLayout(bottom)

    # ------------------------------------------------------------ picker
    def _reload_samples(self):
        checked = self._checked_ids() | self._preselect
        self.sample_list.clear()
        try:
            rows = gx.list_geocork_samples(self.filter_edit.text())
        except Exception as exc:
            QMessageBox.critical(self, "Database Error", f"Could not list samples:\n\n{exc}")
            return
        for r in rows:
            igsn = r.get("SampleIGSN")
            item = QListWidgetItem(f"{r['SampleName']}  [{igsn}]" if igsn
                                   else f"{r['SampleName']}  (no IGSN → register)")
            item.setData(Qt.ItemDataRole.UserRole, int(r["SampleID"]))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if int(r["SampleID"]) in checked
                               else Qt.CheckState.Unchecked)
            self.sample_list.addItem(item)
        self._preselect.clear()

    def _checked_ids(self) -> set:
        out = set()
        for i in range(self.sample_list.count()):
            it = self.sample_list.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                out.add(int(it.data(Qt.ItemDataRole.UserRole)))
        return out

    def _check_list(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.sample_list.count()):
            self.sample_list.item(i).setCheckState(state)

    # ------------------------------------------------------------ prepare
    def _prepare(self):
        ids = sorted(self._checked_ids())
        if not ids:
            QMessageBox.information(self, "No samples", "Tick at least one sample first.")
            return
        self._records.clear()
        failures = []
        for sid in ids:
            try:
                self._records[sid] = gx.load_sample_record(sid)
            except Exception as exc:
                failures.append(f"SampleID {sid}: {exc}")
        if failures:
            QMessageBox.warning(self, "Some samples could not be read", "\n".join(failures))
        if not self._records:
            return

        targets = [(sid, r.igsn) for sid, r in self._records.items() if r.igsn]
        get_sesar_logger().info(
            f"[SESAR export] Preparing {len(self._records)} sample(s) "
            f"[update={len(targets)}, register={len(self._records) - len(targets)}]")
        self._set_busy(True, "Fetching current SESAR records…" if targets else "")
        if targets:
            self._worker = RemoteFetchWorker(self._client, targets, self)
            self._worker.done.connect(self._populate_tree)
            self._worker.start()
        else:
            self._populate_tree({}, {})

    def _populate_tree(self, remotes: dict, errors: dict):
        self._set_busy(False)
        self.tree.blockSignals(True)
        self.tree.clear()
        self._sample_items.clear()
        sesar_code = api.configured_sesar_code()
        obj_type = self.object_type_edit.text().strip()

        for sid, rec in self._records.items():
            register = not rec.igsn
            fields = gx.build_export_fields(rec, sesar_code, obj_type, for_register=register)
            top = QTreeWidgetItem(self.tree)
            top.setData(0, _ROLE_SAMPLE, sid)
            top.setFlags(top.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            action = "Register new sample" if register else f"Update {rec.igsn}"
            top.setText(_COL_FIELD, rec.name)
            top.setText(_COL_VALUE, action)
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)

            if not register and sid in errors:
                top.setText(_COL_NOTE, "Could not fetch SESAR record — not sent")
                top.setToolTip(_COL_NOTE, errors[sid])
                top.setForeground(_COL_NOTE, _ERR)
                top.setCheckState(0, Qt.CheckState.Unchecked)
                top.setDisabled(True)
                self._sample_items[sid] = top
                continue

            if not register:
                remote = remotes.get(sid, {})
                fields = gx.apply_remote(fields, remote)
                if str(remote.get("can_edit")).lower() == "false":
                    top.setText(_COL_NOTE, "SESAR reports you can't edit this sample")
                    top.setForeground(_COL_NOTE, _ERR)

            for fld in fields:
                child = QTreeWidgetItem(top)
                child.setData(0, _ROLE_FIELD, fld)
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable
                               | Qt.ItemFlag.ItemIsEditable)
                child.setText(_COL_FIELD, fld.label)
                child.setToolTip(_COL_FIELD, fld.key)
                child.setText(_COL_VALUE, gx.to_display(fld.value))
                child.setToolTip(_COL_VALUE, gx.to_display(fld.value))
                child.setText(_COL_REMOTE, gx.to_display(fld.remote) if fld.remote_known else "—")
                child.setText(_COL_NOTE, ("derived; " if not fld.direct else "") + fld.note)
                child.setForeground(_COL_NOTE, _GREY)
                child.setCheckState(0, Qt.CheckState.Checked if fld.send else Qt.CheckState.Unchecked)

            n_checked = sum(1 for fl in fields if fl.send)
            top.setCheckState(0, Qt.CheckState.Checked if (register or n_checked)
                              else Qt.CheckState.Unchecked)
            if not register and not n_checked and not top.text(_COL_NOTE):
                top.setText(_COL_NOTE, "No differences from SESAR")
                top.setForeground(_COL_NOTE, _GREY)
            top.setExpanded(register or n_checked > 0)
            self._sample_items[sid] = top

        self.tree.blockSignals(False)
        self.send_btn.setEnabled(bool(self._sample_items))
        self.status_label.setText(f"{len(self._sample_items)} sample(s) ready for review.")

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        """Keep ExportField in sync with edits and checkboxes."""
        fld: gx.ExportField = item.data(0, _ROLE_FIELD)
        if fld is None:
            return
        if column == _COL_VALUE:
            try:
                fld.value = gx.parse_edited(fld.key, item.text(_COL_VALUE))
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid value", str(exc))
                self.tree.blockSignals(True)
                item.setText(_COL_VALUE, gx.to_display(fld.value))
                self.tree.blockSignals(False)
                return
            if fld.remote_known:
                changed = not gx.values_equal(fld.key, fld.value, fld.remote)
                self.tree.blockSignals(True)
                item.setCheckState(0, Qt.CheckState.Checked if changed else Qt.CheckState.Unchecked)
                self.tree.blockSignals(False)
                fld.send = changed
        elif column == 0:
            fld.send = item.checkState(0) == Qt.CheckState.Checked

    # --------------------------------------------------------------- send
    def _collect_jobs(self) -> Tuple[List[dict], List[str]]:
        jobs, problems = [], []
        is_draft = self.draft_check.isChecked()
        for sid, top in self._sample_items.items():
            if top.isDisabled() or top.checkState(0) != Qt.CheckState.Checked:
                continue
            rec = self._records[sid]
            fields = [top.child(i).data(0, _ROLE_FIELD) for i in range(top.childCount())]
            register = not rec.igsn
            payload = gx.build_payload(fields, register=register, is_draft=is_draft)
            if register:
                missing = gx.register_problems(payload)
                if missing:
                    problems.append(f"{rec.name}: missing {', '.join(missing)}")
                    continue
            elif not payload:
                continue
            jobs.append({"sample_id": sid, "name": rec.name, "igsn": rec.igsn,
                         "action": "register" if register else "update",
                         "payload": payload})
        return jobs, problems

    def _send(self):
        if not self._client.has_credentials():
            QMessageBox.warning(self, "No SESAR token",
                                "Sending requires a SESAR JSON Web Token.\n\n"
                                "Add your access and refresh tokens in Settings → SESAR.")
            return
        jobs, problems = self._collect_jobs()
        if problems:
            QMessageBox.warning(self, "Cannot register some samples",
                                "These samples were skipped:\n\n" + "\n".join(problems)
                                + "\n\nFill the missing values (double-click a value to edit), "
                                  "or tick 'Register as drafts'.")
        if not jobs:
            if not problems:
                QMessageBox.information(self, "Nothing to send",
                                        "No samples have checked fields to send.")
            return

        n_up = sum(1 for j in jobs if j["action"] == "update")
        n_reg = len(jobs) - n_up
        env = self._client.environment
        lines = [f"Send to SESAR {env.upper()}?", ""]
        if n_up:
            lines.append(f"• Update {n_up} existing sample(s)")
        if n_reg:
            lines.append(f"• Register {n_reg} new sample(s)"
                         + (" as drafts" if self.draft_check.isChecked() else ""))
        if env == "production":
            lines += ["", "Production registrations mint official, permanent IGSNs."]
        if QMessageBox.question(self, "Confirm send", "\n".join(lines)) \
                != QMessageBox.StandardButton.Yes:
            return

        self._minted.clear()
        self._results: List[Tuple[str, bool, str]] = []
        self._set_busy(True, "Sending…")
        self._worker = SendWorker(self._client, jobs, self)
        self._worker.progress.connect(
            lambda i, n, name: self.status_label.setText(f"Sending {i} of {n}: {name}"))
        self._worker.result.connect(self._on_send_result)
        self._worker.finished_all.connect(self._on_send_finished)
        self._worker.start()

    def _on_send_result(self, sample_id: int, ok: bool, message: str, response):
        top = self._sample_items.get(sample_id)
        rec = self._records.get(sample_id)
        if ok and rec and not rec.igsn and isinstance(response, dict) and response.get("igsn"):
            self._minted.append((sample_id, response["igsn"]))
        if top is not None:
            top.setText(_COL_NOTE, message.splitlines()[0] if message else "")
            top.setToolTip(_COL_NOTE, message)
            top.setForeground(_COL_NOTE, _OK if ok else _ERR)
            if ok:
                top.setCheckState(0, Qt.CheckState.Unchecked)
        self._results.append((rec.name if rec else str(sample_id), ok, message))
        get_sesar_logger().log(20 if ok else 40,
                               f"[SESAR export] {rec.name if rec else sample_id}: {message}")

    def _on_send_finished(self):
        self._set_busy(False)
        writeback_errors = []
        for sid, igsn in self._minted:
            try:
                gx.write_back_igsn(sid, igsn)
                self._records[sid].igsn = igsn
            except Exception as exc:
                writeback_errors.append(f"{self._records[sid].name} → {igsn}: {exc}")

        ok = [r for r in self._results if r[1]]
        bad = [r for r in self._results if not r[1]]
        text = f"{len(ok)} succeeded, {len(bad)} failed."
        if self._minted:
            text += "\n\nNew IGSNs saved to GeoCORK:\n" + "\n".join(
                f"  {self._records[s].name}: {i}" for s, i in self._minted)
        if bad:
            text += "\n\nFailures:\n" + "\n\n".join(f"{n}:\n{m}" for n, _, m in bad[:8])
        if writeback_errors:
            text += ("\n\nIMPORTANT — registered on SESAR but the IGSN could not be saved "
                     "in GeoCORK. Record these manually:\n" + "\n".join(writeback_errors))
        box = QMessageBox.warning if (bad or writeback_errors) else QMessageBox.information
        box(self, "SESAR send complete", text)
        self.status_label.setText(text.splitlines()[0])
        if self._minted:
            self._reload_samples()

    # -------------------------------------------------------------- misc
    def _set_busy(self, busy: bool, message: str = ""):
        self.prepare_btn.setEnabled(not busy)
        self.send_btn.setEnabled(not busy and bool(self._sample_items))
        self.tree.setEnabled(not busy)
        if message:
            self.status_label.setText(message)

    def reject(self):
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(self, "Please wait",
                                    "A SESAR request is still running. Close once it finishes.")
            return
        super().reject()
