#!/usr/bin/env python3
"""
PySide6 GUI to insert sample readings into a PostgreSQL database.

- Samples are loaded from samples.yaml (short_name, epics_pv, phase).
- Each row exposes an editable float_val cell and a per-row "Read" button
  that caget()s just that sample's epics_pv.
- "Read EPICS" reads all rows at once.
- time_date is picked with a calendar/datetime widget (or "Now").
- "Insert" writes one row per sample inside a single transaction.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import psycopg2
import yaml

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QDateTime
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QSpinBox,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPlainTextEdit, QGridLayout, QHBoxLayout,
    QVBoxLayout, QGroupBox, QStatusBar, QDateTimeEdit,
)

from db_config import DB_CONFIG


INSERT_SQL = (
    "INSERT INTO sample "
    "(time_date, reports_id, short_name, pulse_phase, float_val) "
    "VALUES (%s, %s, %s, %s, %s)"
)

DEFAULT_SAMPLES_FILE = Path(__file__).with_name("samples.yaml")

log = logging.getLogger("insert_samples_gui")


# ---------- Shared helpers ----------

def load_samples(path: Path) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"{path}: expected a non-empty list of samples.")
    required = {"short_name", "epics_pv", "phase"}
    for i, entry in enumerate(data):
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"{path}: sample #{i} missing keys: {missing}")
    return data


def read_epics_values(pv_names: List[str], timeout: float = 3.0) -> List[float]:
    try:
        from epics import caget
    except ImportError as exc:
        raise RuntimeError(
            "pyepics is required to read EPICS PVs. Install with `pip install pyepics`."
        ) from exc
    out = []
    for pv in pv_names:
        val = caget(pv, timeout=timeout)
        if val is None:
            raise RuntimeError(f"Failed to read EPICS PV: {pv}")
        out.append(float(val))
    return out


# ---------- Logging bridge ----------

class LogBridge(QObject):
    message = Signal(str, str)  # level, formatted message


class QtLogHandler(logging.Handler):
    def __init__(self, bridge: LogBridge):
        super().__init__()
        self.bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        text = f"{ts} {record.levelname:<7} {record.getMessage()}"
        self.bridge.message.emit(record.levelname, text)


# ---------- Worker objects ----------

class EpicsWorker(QObject):
    """Reads one or more PVs. Emits per-PV updates so the table can fill incrementally."""

    one_done = Signal(int, float)    # row_index, value
    one_failed = Signal(int, str)    # row_index, error
    finished = Signal()

    def __init__(self, pv_targets: List[tuple]):
        """pv_targets: list of (row_index, pv_name)."""
        super().__init__()
        self.pv_targets = pv_targets

    @Slot()
    def run(self) -> None:
        try:
            from epics import caget
        except ImportError:
            for idx, _ in self.pv_targets:
                self.one_failed.emit(
                    idx,
                    "pyepics not installed (pip install pyepics)",
                )
            self.finished.emit()
            return

        for idx, pv in self.pv_targets:
            try:
                val = caget(pv, timeout=3.0)
                if val is None:
                    self.one_failed.emit(idx, f"timeout reading {pv}")
                else:
                    self.one_done.emit(idx, float(val))
            except Exception as exc:
                self.one_failed.emit(idx, f"{pv}: {exc}")
        self.finished.emit()


class InsertWorker(QObject):
    finished = Signal(int)
    failed = Signal(str)
    row_done = Signal(int, int)

    def __init__(self, rows: list):
        super().__init__()
        self.rows = rows

    @Slot()
    def run(self) -> None:
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    total = len(self.rows)
                    for i, r in enumerate(self.rows, start=1):
                        cur.execute(INSERT_SQL, r)
                        self.row_done.emit(i, total)
            self.finished.emit(len(self.rows))
        except psycopg2.Error as exc:
            self.failed.emit(str(exc))


# ---------- Main window ----------

class MainWindow(QMainWindow):
    COL_SHORT, COL_PHASE, COL_PV, COL_VALUE, COL_READ = range(5)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sample Insert")
        self.resize(880, 640)

        self.samples_file = DEFAULT_SAMPLES_FILE
        self.samples: List[dict] = []
        self._threads: list = []

        self._build_ui()
        self._setup_logging()
        self._try_load_samples(self.samples_file)

    # ----- layout -----

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Parameters
        form_box = QGroupBox("Parameters")
        form = QGridLayout(form_box)

        form.addWidget(QLabel("reports_id:"), 0, 0)
        self.reports_id_spin = QSpinBox()
        self.reports_id_spin.setRange(1, 1_000_000_000)
        self.reports_id_spin.setValue(1)
        form.addWidget(self.reports_id_spin, 0, 1)

        form.addWidget(QLabel("time_date:"), 0, 2)
        self.time_edit = QDateTimeEdit()
        self.time_edit.setCalendarPopup(True)
        self.time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.time_edit.setTimeSpec(Qt.UTC)
        self.time_edit.setDateTime(QDateTime.currentDateTimeUtc())
        form.addWidget(self.time_edit, 0, 3)

        self.now_btn = QPushButton("Now")
        self.now_btn.clicked.connect(self._fill_now)
        form.addWidget(self.now_btn, 0, 4)

        self.use_now_cb = QCheckBox("Use current time at insert")
        self.use_now_cb.setToolTip(
            "If checked, time_date is captured at the moment Insert is clicked, "
            "ignoring the value above."
        )
        form.addWidget(self.use_now_cb, 0, 5)

        form.addWidget(QLabel("samples file:"), 1, 0)
        self.samples_path_edit = QLineEdit(str(self.samples_file))
        form.addWidget(self.samples_path_edit, 1, 1, 1, 3)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_samples)
        form.addWidget(self.browse_btn, 1, 4)
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.clicked.connect(self._reload_samples)
        form.addWidget(self.reload_btn, 1, 5)

        form.setColumnStretch(3, 1)
        root.addWidget(form_box)

        # Samples table
        table_box = QGroupBox("Samples")
        table_layout = QVBoxLayout(table_box)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["short_name", "pulse_phase", "epics_pv", "float_val", ""])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_SHORT, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_PHASE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_PV, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_VALUE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_READ, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        table_layout.addWidget(self.table)
        root.addWidget(table_box, stretch=1)

        # Actions
        actions = QHBoxLayout()
        self.dry_run_cb = QCheckBox("Dry run (don't write to DB)")
        actions.addWidget(self.dry_run_cb)
        actions.addStretch(1)
        self.read_epics_btn = QPushButton("Read EPICS (all)")
        self.read_epics_btn.clicked.connect(self._on_read_all_epics)
        actions.addWidget(self.read_epics_btn)
        self.clear_btn = QPushButton("Clear values")
        self.clear_btn.clicked.connect(self._on_clear)
        actions.addWidget(self.clear_btn)
        self.insert_btn = QPushButton("Insert")
        self.insert_btn.setDefault(True)
        self.insert_btn.clicked.connect(self._on_insert)
        actions.addWidget(self.insert_btn)
        root.addLayout(actions)

        # Log
        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_box, stretch=1)

        self.setStatusBar(QStatusBar(self))

        # File menu
        file_menu = self.menuBar().addMenu("&File")
        open_act = QAction("&Open samples...", self)
        open_act.triggered.connect(self._browse_samples)
        file_menu.addAction(open_act)
        reload_act = QAction("&Reload samples", self)
        reload_act.triggered.connect(self._reload_samples)
        file_menu.addAction(reload_act)
        file_menu.addSeparator()
        quit_act = QAction("&Quit", self)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

    # ----- logging -----

    def _setup_logging(self) -> None:
        self.log_bridge = LogBridge()
        self.log_bridge.message.connect(self._append_log)
        handler = QtLogHandler(self.log_bridge)
        logging.basicConfig(level=logging.INFO, handlers=[handler])

    @Slot(str, str)
    def _append_log(self, level: str, text: str) -> None:
        self.log_view.appendPlainText(text)
        if level in ("ERROR", "CRITICAL"):
            self.statusBar().showMessage(text, 5000)

    # ----- samples -----

    def _try_load_samples(self, path: Path) -> None:
        try:
            samples = load_samples(path)
        except Exception as exc:
            QMessageBox.critical(self, "Load failed",
                                 f"Could not load {path}:\n{exc}")
            return
        self.samples_file = path
        self.samples = samples
        self.samples_path_edit.setText(str(path))
        self._populate_table(samples)
        log.info("Loaded %d sample(s) from %s", len(samples), path)

    def _populate_table(self, samples: List[dict]) -> None:
        self.table.setRowCount(len(samples))
        for i, s in enumerate(samples):
            for col, key in ((self.COL_SHORT, "short_name"),
                             (self.COL_PHASE, "phase"),
                             (self.COL_PV, "epics_pv")):
                item = QTableWidgetItem(str(s[key]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, col, item)
            value_item = QTableWidgetItem("")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, self.COL_VALUE, value_item)

            # Per-row Read button
            read_btn = QPushButton("Read")
            read_btn.setToolTip(f"caget {s['epics_pv']}")
            read_btn.clicked.connect(lambda _=False, row=i: self._on_read_one(row))
            self.table.setCellWidget(i, self.COL_READ, read_btn)

    def _browse_samples(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select samples YAML",
            str(self.samples_file.parent),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if path:
            self._try_load_samples(Path(path))

    def _reload_samples(self) -> None:
        self._try_load_samples(Path(self.samples_path_edit.text()))

    # ----- actions -----

    def _fill_now(self) -> None:
        self.time_edit.setDateTime(QDateTime.currentDateTimeUtc())

    def _on_clear(self) -> None:
        for i in range(self.table.rowCount()):
            self.table.item(i, self.COL_VALUE).setText("")

    def _row_value(self, i: int) -> float:
        text = self.table.item(i, self.COL_VALUE).text().strip()
        if not text:
            raise ValueError(
                f"{self.samples[i]['short_name']}: value is empty")
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(
                f"{self.samples[i]['short_name']}: '{text}' is not a number"
            ) from exc

    def _set_row_value(self, i: int, val: float) -> None:
        self.table.item(i, self.COL_VALUE).setText(f"{val:g}")

    def _set_row_button_enabled(self, i: int, enabled: bool) -> None:
        btn = self.table.cellWidget(i, self.COL_READ)
        if isinstance(btn, QPushButton):
            btn.setEnabled(enabled)

    # ----- EPICS: single row -----

    def _on_read_one(self, row: int) -> None:
        if row >= len(self.samples):
            return
        pv = self.samples[row]["epics_pv"]
        self._set_row_button_enabled(row, False)
        worker = EpicsWorker([(row, pv)])
        worker.one_done.connect(self._on_one_epics_done)
        worker.one_failed.connect(self._on_one_epics_failed)
        worker.finished.connect(lambda r=row: self._set_row_button_enabled(r, True))
        self._start_worker(worker)

    # ----- EPICS: all rows -----

    def _on_read_all_epics(self) -> None:
        if not self.samples:
            return
        targets = [(i, s["epics_pv"]) for i, s in enumerate(self.samples)]
        self.read_epics_btn.setEnabled(False)
        for i in range(len(self.samples)):
            self._set_row_button_enabled(i, False)

        worker = EpicsWorker(targets)
        worker.one_done.connect(self._on_one_epics_done)
        worker.one_failed.connect(self._on_one_epics_failed)
        worker.finished.connect(self._on_read_all_done)
        self._start_worker(worker)

    @Slot()
    def _on_read_all_done(self) -> None:
        self.read_epics_btn.setEnabled(True)
        for i in range(len(self.samples)):
            self._set_row_button_enabled(i, True)

    @Slot(int, float)
    def _on_one_epics_done(self, row: int, val: float) -> None:
        self._set_row_value(row, val)
        log.info("EPICS %s = %g", self.samples[row]["epics_pv"], val)

    @Slot(int, str)
    def _on_one_epics_failed(self, row: int, msg: str) -> None:
        log.error("EPICS read failed for row %d: %s", row, msg)
        self.statusBar().showMessage(f"EPICS error: {msg}", 5000)

    # ----- Insert -----

    def _resolve_time_date(self) -> datetime:
        if self.use_now_cb.isChecked():
            return datetime.now(timezone.utc)
        qdt = self.time_edit.dateTime()
        # QDateTimeEdit was created with Qt.UTC, so toPython() returns a naive
        # datetime representing UTC. Tag it as UTC explicitly.
        py = qdt.toPython()
        if py.tzinfo is None:
            py = py.replace(tzinfo=timezone.utc)
        return py

    def _on_insert(self) -> None:
        if not self.samples:
            QMessageBox.warning(self, "No samples", "Load a samples file first.")
            return

        try:
            float_vals = [self._row_value(i) for i in range(len(self.samples))]
            reports_id = self.reports_id_spin.value()
            time_date = self._resolve_time_date()
        except Exception as exc:
            QMessageBox.critical(self, "Invalid input", str(exc))
            return

        rows = [
            (time_date, reports_id, s["short_name"], s["phase"], fv)
            for s, fv in zip(self.samples, float_vals)
        ]

        for i, r in enumerate(rows, start=1):
            log.info(
                "Row %d/%d: time_date=%s reports_id=%d short_name=%r "
                "pulse_phase=%r float_val=%g",
                i, len(rows), r[0].isoformat(), r[1], r[2], r[3], r[4],
            )

        if self.dry_run_cb.isChecked():
            log.warning("Dry run: nothing written to the database.")
            QMessageBox.information(
                self, "Dry run", f"{len(rows)} row(s) prepared, not written.")
            return

        self.insert_btn.setEnabled(False)
        worker = InsertWorker(rows)
        worker.row_done.connect(self._on_row_inserted)
        worker.finished.connect(self._on_insert_done)
        worker.failed.connect(self._on_insert_failed)
        self._start_worker(worker)

    @Slot(int, int)
    def _on_row_inserted(self, i: int, total: int) -> None:
        log.info("Inserted row %d/%d", i, total)
        self.statusBar().showMessage(f"Inserted {i}/{total}", 2000)

    @Slot(int)
    def _on_insert_done(self, n: int) -> None:
        log.info("Inserted %d row(s) into sample.", n)
        QMessageBox.information(self, "Done", f"Inserted {n} row(s).")
        self.insert_btn.setEnabled(True)

    @Slot(str)
    def _on_insert_failed(self, msg: str) -> None:
        log.error("Database error: %s", msg)
        QMessageBox.critical(self, "Database error", msg)
        self.insert_btn.setEnabled(True)

    # ----- worker plumbing -----

    def _start_worker(self, worker: QObject) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        for sig_name in ("finished", "failed"):
            sig = getattr(worker, sig_name, None)
            if sig is not None:
                sig.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda t=thread: self._threads.remove(t) if t in self._threads else None
        )
        self._threads.append(thread)
        thread.start()


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
