"""
Spike detection + interactive validation, with HDF5 write-back.
Optional refinements

    Read-only source file: if you don't want to touch the original, change the save path to a sidecar:

    results_path = self.path_h5.replace(".h5", "_results.h5")
    with h5py.File(results_path, "a") as h5: ...

    Batch validation across many files: add Previous/Next buttons that reload self.x, self.t, and call _populate_plot().
    Undo button: stash self.trigger_idx and self.peak_amp in a list before each save, restore on click.

"""
import sys
import argparse
import numpy as np
import h5py
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from scipy.signal import find_peaks
from scipy.ndimage import median_filter, uniform_filter1d
from pathlib import Path


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
#PATH_H5  = "your_file.h5"
SIG_KEY  = "raw-data/control-room/rohde-schwarz/waveforms/C1"
TIME_KEY = "raw-data/control-room/rohde-schwarz/waveforms/TIME"

# Where to write the validated results inside the HDF5 file
RESULTS_GROUP = "analysis/C1"

# ----------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------
def find_last_pretrigger_spike(x, trigger_idx, edge_guard=50_000,
                               baseline_window=5001, n_sigma=5):
    pre = x[:max(0, trigger_idx - edge_guard)]
    if len(pre) < baseline_window:
        return None, 0.0
    baseline = median_filter(pre, size=baseline_window)
    residual = pre - baseline
    noise = 1.4826 * np.median(np.abs(residual - np.median(residual)))
    peaks, _ = find_peaks(
        np.abs(residual),
        height=n_sigma * noise,
        prominence=(n_sigma - 2) * noise,
        distance=10_000,
    )
    if len(peaks) == 0:
        return None, noise
    return int(peaks[-1]), float(noise)


def compute_peak_amplitude(x, spike_window=2001, smooth_window=501):
    smooth = uniform_filter1d(median_filter(x, size=spike_window),
                              size=smooth_window)
    idx = int(np.argmax(smooth))
    return idx, float(smooth[idx])


# ----------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------
class SpikeValidator(QtWidgets.QMainWindow):
    def __init__(self, path_h5, sig_key, time_key, results_group, write_path=None):
        super().__init__()
        self.path_h5 = path_h5
        self.write_path = write_path or path_h5   # default: write to same file
        self.sig_key = sig_key
        self.time_key = time_key
        self.results_group = results_group

        # --- Load data ---
        with h5py.File(path_h5, "r") as h5:
            self.x = h5[sig_key][:].astype(np.float32)
            self.t = h5[time_key][:].astype(np.float64)

        self.trigger_idx = int(np.searchsorted(self.t, 0.0))
        self.last_spike, self.noise = find_last_pretrigger_spike(
            self.x, self.trigger_idx
        )
        self.peak_idx, self.peak_amp = compute_peak_amplitude(self.x)

        self._build_ui()
        self._populate_plot()
        self._update_status()

    # ------------------------------------------------------------------
    def _build_ui(self):
        self.setWindowTitle(f"Spike validation — {self.path_h5}")
        self.resize(1400, 850)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Plot area
        pg.setConfigOptions(antialias=False)
        self.glw = pg.GraphicsLayoutWidget()
        layout.addWidget(self.glw, stretch=1)

        self.p1 = self.glw.addPlot(row=0, col=0,
                                   title="Signal with trigger & peak markers")
        self.p1.setDownsampling(auto=True, mode='peak')
        self.p1.setClipToView(True)
        self.p1.setLabel('bottom', 'Sample index')

        # Status label + button row
        bar = QtWidgets.QHBoxLayout()
        layout.addLayout(bar)

        self.status = QtWidgets.QLabel()
        self.status.setStyleSheet("font-family: monospace;")
        bar.addWidget(self.status, stretch=1)

        self.btn_recompute = QtWidgets.QPushButton("Recompute")
        self.btn_recompute.clicked.connect(self.recompute)
        bar.addWidget(self.btn_recompute)

        self.btn_validate = QtWidgets.QPushButton("Validate && Save to HDF5")
        self.btn_validate.setStyleSheet(
            "background-color: #2a7; color: white; font-weight: bold; padding: 6px 14px;"
        )
        self.btn_validate.clicked.connect(self.validate_and_save)
        bar.addWidget(self.btn_validate)

    # ------------------------------------------------------------------
    def _populate_plot(self):
        self.p1.clear()
        self.p1.plot(self.x, pen=pg.mkPen('w', width=1))

        # Trigger line (green dashed)
        self.trigger_line = pg.InfiniteLine(
            pos=self.trigger_idx, angle=90, movable=True,
            pen=pg.mkPen('g', width=2, style=QtCore.Qt.PenStyle.DashLine),
            label='trigger (t=0)', labelOpts={'color': 'g'},
        )
        self.trigger_line.sigPositionChanged.connect(self._on_trigger_moved)
        self.p1.addItem(self.trigger_line)

        # Last pre-trigger spike marker (yellow circle)
        if self.last_spike is not None:
            self.spike_marker = pg.ScatterPlotItem(
                x=[self.last_spike], y=[self.x[self.last_spike]],
                pen=pg.mkPen('y', width=3), brush=None,
                symbol='o', size=18,
            )
            self.p1.addItem(self.spike_marker)
        else:
            self.spike_marker = None

        # Peak amplitude horizontal + cross marker (magenta)
        self.peak_hline = pg.InfiniteLine(
            pos=self.peak_amp, angle=0, movable=True,
            pen=pg.mkPen('m', width=2, style=QtCore.Qt.PenStyle.DotLine),
            label='peak amp', labelOpts={'color': 'm'},
        )
        self.peak_hline.sigPositionChanged.connect(self._on_peak_moved)
        self.p1.addItem(self.peak_hline)

        self.peak_marker = pg.ScatterPlotItem(
            x=[self.peak_idx], y=[self.peak_amp],
            pen=pg.mkPen('m', width=3), brush=None,
            symbol='+', size=22,
        )
        self.p1.addItem(self.peak_marker)

    # ------------------------------------------------------------------
    def _on_trigger_moved(self, line):
        self.trigger_idx = int(np.clip(line.value(), 0, len(self.x) - 1))
        self._update_status()

    def _on_peak_moved(self, line):
        self.peak_amp = float(line.value())
        self._update_status()

    # ------------------------------------------------------------------
    def _update_status(self):
        t_trig = self.t[self.trigger_idx]
        if self.last_spike is not None:
            t_spike = self.t[self.last_spike]
            dt_to_trig = (self.trigger_idx - self.last_spike) * float(
                np.median(np.diff(self.t))
            )
            spike_txt = (f"pre-spike @ sample {self.last_spike:,} "
                         f"t={t_spike*1e6:+.2f} µs  "
                         f"(Δ={dt_to_trig*1e6:.2f} µs before trigger)")
        else:
            spike_txt = "pre-spike: NOT FOUND"

        self.status.setText(
            f"trigger @ sample {self.trigger_idx:,}  t={t_trig*1e6:+.2f} µs   |   "
            f"{spike_txt}   |   "
            f"peak amp = {self.peak_amp:.4f}   |   "
            f"noise (MAD) = {self.noise:.5f}"
        )

    # ------------------------------------------------------------------
    def recompute(self):
        """Re-run detection with the current (possibly user-moved) trigger."""
        self.last_spike, self.noise = find_last_pretrigger_spike(
            self.x, self.trigger_idx
        )
        self.peak_idx, self.peak_amp = compute_peak_amplitude(self.x)
        self._populate_plot()
        self._update_status()

    # ------------------------------------------------------------------
    def validate_and_save(self):
        """Write trigger_idx, peak_amp, etc. back into the HDF5 file."""
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm save",
            f"Write the following to '{self.write_path}'?\n\n"
            f"  group: {self.results_group}\n"
            f"  trigger_index   = {self.trigger_idx}\n"
            f"  trigger_time    = {self.t[self.trigger_idx]:.6e} s\n"
            f"  peak_amplitude  = {self.peak_amp:.6f}\n"
            f"  peak_index      = {self.peak_idx}\n"
            f"  pre_spike_index = {self.last_spike}\n"
            f"  noise_mad       = {self.noise:.6e}",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        try:
            with h5py.File(self.path_h5, "a") as h5:   # "a" = read/write, create if missing
                grp = h5.require_group(self.results_group)

                def write_scalar(name, value, dtype=None):
                    if name in grp:
                        del grp[name]
                    grp.create_dataset(name, data=value, dtype=dtype)

                write_scalar("trigger_index", self.trigger_idx, dtype="int64")
                write_scalar("trigger_time", float(self.t[self.trigger_idx]),
                             dtype="float64")
                write_scalar("peak_amplitude", self.peak_amp, dtype="float64")
                write_scalar("peak_index", self.peak_idx, dtype="int64")
                if self.last_spike is not None:
                    write_scalar("pre_spike_index", self.last_spike, dtype="int64")
                    write_scalar("pre_spike_time",
                                 float(self.t[self.last_spike]), dtype="float64")
                write_scalar("noise_mad", self.noise, dtype="float64")

                # Provenance attributes
                grp.attrs["validated"] = True
                grp.attrs["validated_by"] = "SpikeValidator"
                grp.attrs["validated_at"] = np.bytes_(
                    QtCore.QDateTime.currentDateTimeUtc().toString(
                        QtCore.Qt.DateFormat.ISODate
                    )
                )
                grp.attrs["source_signal"] = np.bytes_(self.sig_key)

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Save failed", f"Could not write to HDF5:\n\n{e}"
            )
            return

        QtWidgets.QMessageBox.information(
            self, "Saved",
            f"Results written to '{self.results_group}' in {self.path_h5}.",
        )


# ----------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Interactive spike & peak validator for Rohde & Schwarz HDF5 waveforms."
    )
    parser.add_argument(
        "path_h5",
        type=Path,
        help="Path to the HDF5 file containing the waveform.",
    )
    parser.add_argument(
        "--sig-key",
        default="raw-data/control-room/rohde-schwarz/waveforms/C1",
        help="HDF5 path to the signal dataset (default: %(default)s).",
    )
    parser.add_argument(
        "--time-key",
        default="raw-data/control-room/rohde-schwarz/waveforms/TIME",
        help="HDF5 path to the time dataset (default: %(default)s).",
    )
    parser.add_argument(
        "--results-group",
        default="analysis/C1",
        help="HDF5 group where validated results will be written "
             "(default: %(default)s).",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Write results to a sidecar file '<name>_results.h5' "
             "instead of modifying the original.",
    )
    args = parser.parse_args()

    if not args.path_h5.exists():
        parser.error(f"File not found: {args.path_h5}")
    if not args.path_h5.is_file():
        parser.error(f"Not a file: {args.path_h5}")

    return args


def main():
    args = parse_args()

    # Optional sidecar mode
    write_path = args.path_h5
    if args.read_only:
        write_path = args.path_h5.with_name(
            args.path_h5.stem + "_results.h5"
        )

    app = QtWidgets.QApplication(sys.argv)
    win = SpikeValidator(
        path_h5=str(args.path_h5),
        sig_key=args.sig_key,
        time_key=args.time_key,
        results_group=args.results_group,
        write_path=str(write_path),
    )
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""
    # Basic: edit the file in place
python validator.py /data/shot_12345.h5

# Custom dataset paths
python validator.py /data/shot_12345.h5 --sig-key raw-data/.../C2

# Don't touch the source — write to shot_12345_results.h5 next to it
python validator.py /data/shot_12345.h5 --read-only

# See all options
python validator.py --help
"""
