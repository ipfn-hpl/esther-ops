#!/usr/bin/env python3
"""
HDF5 Oscilloscope Data Viewer using PyQtGraph.

Opens HDF5 files created by the CSV to HDF5 converter and displays
interactive waveform plots.
"""

import sys
from pathlib import Path

import h5py
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets


class WaveformViewer(QtWidgets.QMainWindow):
    """Main window for viewing oscilloscope waveforms from HDF5 files."""

    # Distinct colors for channels
    COLORS = [
        (255, 255, 0),  # Yellow (CH1)
        (0, 255, 255),  # Cyan (CH2)
        (255, 0, 255),  # Magenta (CH3)
        (0, 255, 0),  # Green (CH4)
        (255, 128, 0),  # Orange
        (128, 128, 255),  # Light blue
        (255, 128, 128),  # Light red
        (128, 255, 128),  # Light green
    ]

    def __init__(self, h5_path: str | None = None):
        super().__init__()
        self.setWindowTitle("HDF5 Waveform Viewer")
        self.resize(1200, 800)

        self.h5_file = None
        self.plots = []
        self.curves = []

        self._setup_ui()

        if h5_path:
            self.load_file(h5_path)

    def _setup_ui(self):
        """Set up the user interface."""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()

        self.open_btn = QtWidgets.QPushButton("Open HDF5...")
        self.open_btn.clicked.connect(self._open_file_dialog)
        toolbar.addWidget(self.open_btn)

        self.file_label = QtWidgets.QLabel("No file loaded")
        toolbar.addWidget(self.file_label)

        toolbar.addStretch()

        # Channel visibility checkboxes
        self.channel_checks = {}
        self.checks_layout = QtWidgets.QHBoxLayout()
        toolbar.addLayout(self.checks_layout)

        layout.addLayout(toolbar)

        # Plot widget
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground("k")
        layout.addWidget(self.plot_widget)

        # Info bar
        self.info_label = QtWidgets.QLabel("")
        layout.addWidget(self.info_label)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        open_action = file_menu.addAction("Open...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file_dialog)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

    def _open_file_dialog(self):
        """Open file dialog to select HDF5 file."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open HDF5 File", "", "HDF5 Files (*.h5 *.hdf5);;All Files (*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        """Load and display waveforms from HDF5 file."""
        path = Path(path)

        if self.h5_file:
            self.h5_file.close()

        try:
            self.h5_file = h5py.File(path, "r")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")
            return

        self.file_label.setText(path.name)
        self._clear_plots()
        self._load_waveforms()

    def _clear_plots(self):
        """Clear existing plots and checkboxes."""
        self.plot_widget.clear()
        self.plots.clear()
        self.curves.clear()

        for cb in self.channel_checks.values():
            self.checks_layout.removeWidget(cb)
            cb.deleteLater()
        self.channel_checks.clear()

    def _load_waveforms(self):
        """Load waveforms from the HDF5 file and create plots."""
        hf = self.h5_file

        # Determine structure (waveforms group or flat)
        key = "raw-data/experimental-hall/tektronix/waveforms"
        if key in hf:
            data_grp = hf[key]
        else:
            data_grp = hf

        # Find time array and channels
        time_data = None
        time_unit = "s"
        channels = []

        for name in data_grp.keys():
            ds = data_grp[name]
            if not isinstance(ds, h5py.Dataset):
                continue

            if name.upper() in ("TIME", "T", "S") or "time" in name.lower():
                time_data = ds[:]
                time_unit = ds.attrs.get("unit", "s")
            else:
                unit = ds.attrs.get("unit", "V")
                channels.append({"name": name, "data": ds[:], "unit": unit})

        # If no explicit time column, check for 's' column (simple format)
        if time_data is None and "s" in data_grp:
            time_data = data_grp["s"][:]
            time_unit = data_grp["s"].attrs.get("unit", "s")

        # Generate time array if not found
        if time_data is None and channels:
            time_data = np.arange(len(channels[0]["data"]))
            time_unit = "samples"

        if not channels:
            self.info_label.setText("No waveform data found in file")
            return

        # Display metadata
        info_parts = [f"Samples: {len(time_data):,}"]
        if "metadata" in hf:
            meta = hf["metadata"]
            if "Sample Interval" in meta.attrs:
                info_parts.append(
                    f"Sample Interval: {meta.attrs['Sample Interval']:.2e} s"
                )
            if "Model" in meta.attrs:
                info_parts.append(f"Model: {meta.attrs['Model']}")
        self.info_label.setText(" | ".join(info_parts))

        # Create plots - one per channel, linked X axis
        first_plot = None

        for i, ch in enumerate(channels):
            color = self.COLORS[i % len(self.COLORS)]

            # Create plot
            plot = self.plot_widget.addPlot(row=i, col=0)
            plot.setLabel("left", ch["name"], units=ch["unit"])
            plot.setLabel("bottom", "Time", units=time_unit)
            plot.showGrid(x=True, y=True, alpha=0.3)
            plot.addLegend()

            # Link X axis to first plot
            if first_plot is None:
                first_plot = plot
            else:
                plot.setXLink(first_plot)

            # Plot data with downsampling for performance
            curve = plot.plot(
                time_data,
                ch["data"],
                pen=pg.mkPen(color=color, width=1),
                name=ch["name"],
                downsample=max(1, len(time_data) // 10000),
                downsampleMethod="peak",
            )

            self.plots.append(plot)
            self.curves.append(curve)

            # Channel visibility checkbox
            cb = QtWidgets.QCheckBox(ch["name"])
            cb.setChecked(True)
            cb.setStyleSheet(f"color: rgb{color};")
            cb.stateChanged.connect(
                lambda state, p=plot: p.setVisible(
                    state == QtCore.Qt.CheckState.Checked.value
                )
            )
            self.checks_layout.addWidget(cb)
            self.channel_checks[ch["name"]] = cb

    def closeEvent(self, event):
        """Clean up on close."""
        if self.h5_file:
            self.h5_file.close()
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark theme
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, pg.QtGui.QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.WindowText, pg.QtGui.QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.Base, pg.QtGui.QColor(25, 25, 25))
    palette.setColor(palette.ColorRole.Text, pg.QtGui.QColor(255, 255, 255))
    palette.setColor(palette.ColorRole.Button, pg.QtGui.QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ButtonText, pg.QtGui.QColor(255, 255, 255))
    app.setPalette(palette)

    # Load file from command line if provided
    h5_path = sys.argv[1] if len(sys.argv) > 1 else None

    viewer = WaveformViewer(h5_path)
    viewer.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
