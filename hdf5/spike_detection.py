"""
Spike detection on a decaying signal with periodic flash-lamp interference.
"""
import sys
import numpy as np
import pyqtgraph as pg
import h5py
import argparse
from pyqtgraph.Qt import QtWidgets, QtCore
from scipy.signal import find_peaks
from scipy.ndimage import median_filter
from pathlib import Path

from scipy.signal import find_peaks
from scipy.ndimage import median_filter, uniform_filter1d

def find_last_pretrigger_spike(x, trigger_idx, edge_guard=50_000,
                                baseline_window=5001, n_sigma=5):
    """Return the sample index of the spike just before the trigger."""
    pre = x[:trigger_idx - edge_guard]
    baseline = median_filter(pre, size=baseline_window)
    residual = pre - baseline

    # MAD-based noise estimate, robust to the spikes themselves
    noise = 1.4826 * np.median(np.abs(residual - np.median(residual)))

    peaks, props = find_peaks(
        np.abs(residual),                  # bipolar spikes
        height=n_sigma * noise,
        prominence=(n_sigma - 2) * noise,
        distance=10_000,
    )
    if len(peaks) == 0:
        return None, noise, peaks

    last_peak = peaks[-1]                  # closest to trigger
    return last_peak, noise, peaks


def find_trigger(x, smooth=1001):
    """Find the rising edge by looking for the max derivative."""
    # Smooth first so noise doesn't dominate the derivative
    from scipy.ndimage import uniform_filter1d
    smoothed = uniform_filter1d(x.astype(np.float32), size=smooth)
    deriv = np.diff(smoothed)
    return int(np.argmax(deriv))

def detect_spikes_two_regions(x, trigger_idx, edge_guard=50_000,
                              baseline_window=5001):
    """
    Detect spikes both before and after the trigger edge.
    
    Parameters
    ----------
    x : 1D array
    trigger_idx : int
        Approximate sample index of the rising edge.
    edge_guard : int
        Samples to exclude on either side of the trigger
        (the rising edge itself isn't a spike).
    """
    n = len(x)

    # --- Pre-trigger region: roughly flat, low amplitude ---
    pre = x[:trigger_idx - edge_guard]
    pre_baseline = median_filter(pre, size=baseline_window)
    pre_residual = pre - pre_baseline
    # Threshold from local noise (robust: median absolute deviation)
    pre_noise = 1.4826 * np.median(np.abs(pre_residual - np.median(pre_residual)))
    pre_peaks, _ = find_peaks(
        np.abs(pre_residual),          # spikes can be + or - here
        height=5 * pre_noise,          # 5 sigma above noise
        distance=10_000,               # adjust to expected spacing
        prominence=3 * pre_noise,
    )

    # --- Post-trigger region: decaying, larger spikes ---
    post_start = trigger_idx + edge_guard
    post = x[post_start:]
    post_baseline = median_filter(post, size=baseline_window)
    post_residual = post - post_baseline
    post_noise = 1.4826 * np.median(np.abs(post_residual - np.median(post_residual)))
    post_peaks, _ = find_peaks(
        post_residual,
        height=5 * post_noise,
        distance=100_000,
        prominence=3 * post_noise,
    )

    # --- Merge back into absolute sample indices ---
    all_peaks = np.concatenate([pre_peaks, post_peaks + post_start])

    # Build a full residual for plotting (same length as x)
    residual = np.zeros_like(x, dtype=np.float32)
    residual[:len(pre_residual)] = pre_residual
    residual[post_start:post_start + len(post_residual)] = post_residual

    return all_peaks, residual, (pre_noise, post_noise)

def detect_spikes(x, start=1_600_000, baseline_window=5001,
                  height=0.2, distance=100_000, prominence=0.15):
    """Detrend with a median filter and find spikes in the residual."""
    x_work = x[start:]
    baseline = median_filter(x_work, size=baseline_window)
    residual = x_work - baseline

    peaks, props = find_peaks(
        residual,
        height=height,
        distance=distance,
        prominence=prominence,
    )
    return peaks, residual, baseline


def main():
    parser = argparse.ArgumentParser(
        description="Script to find spikes and peak Esther Shot data stored in HDF5 files"
    )

    parser.add_argument(
        "-f",
        "--file_h5",
        type=str,
        help="File to read",
        default="data_with_metadata.h5",
    )
    args = parser.parse_args()
    path_h5 = Path(args.file_h5)
    #path_h5 = "your_file.h5"
    sig_key  = "raw-data/control-room/rohde-schwarz/waveforms/C1"
    time_key = "raw-data/control-room/rohde-schwarz/waveforms/TIME"

    with h5py.File(path_h5, "r") as h5:
        x = h5[sig_key][:]   # loads the whole dataset into RAM as a numpy array
        t = h5[time_key][:]  #
    # --- load your signal here ---
    # Replace with your actual data loading
    # x = np.load("signal.npy")
    # For demo:
    """
    n = 10_000_000
    t = np.arange(n)
    x = np.zeros(n, dtype=np.float32)
    rise = 1_500_000
    x[rise:] = 7 * np.exp(-(t[rise:] - rise) / 3e6)
    # add periodic spikes
    for k, pos in enumerate(range(rise + 200_000, n, 400_000)):
        x[pos:pos+200] += 0.5 * np.exp(-k * 0.1)
    x += np.random.randn(n).astype(np.float32) * 0.02
    """
    # Sample where time crosses zero (the trigger)
    trigger_idx = int(np.searchsorted(t, 0.0))
    print(f"Trigger (t=0) at sample {trigger_idx:,}, t[{trigger_idx}] = {t[trigger_idx]:.3e} s")


# Sample period
    dt = float(np.median(np.diff(t)))
    fs = 1.0 / dt
    print(f"Sample period: {dt:.3e} s  |  fs: {fs:.3g} Hz")

    # --- analysis ---
    # --- Find pre trigger spike ---
    last_spike, noise, all_pre_peaks = find_last_pretrigger_spike(x, trigger_idx)
    if last_spike is not None:
        dt_to_trigger = (trigger_idx - last_spike) * dt
        print(f"Last pre-trigger spike: sample {last_spike:,}, "
            f"t = {t[last_spike]:.3e} s  "
            f"({dt_to_trigger*1e6:.2f} µs before trigger)")
    else:
        print("No pre-trigger spike found — try lowering n_sigma")

    # --- Find post trigger ---
    # start = 1_600_000
    #peaks, residual, baseline = detect_spikes(x, start=start)
    #peak_x = peaks + start
    #peak_y = x[peak_x]


    peaks, residual, (pre_noise, post_noise) = detect_spikes_two_regions(
        x, trigger_idx=trigger_idx
    )
    peak_x = peaks
    peak_y = x[peaks]
    spacings = np.diff(peaks)
    print(f"Found {len(peaks)} spikes")
    if len(spacings):
        print(f"Mean spacing: {spacings.mean():.1f} samples "
              f"(std {spacings.std():.1f})")

    print(f"Pre-trigger noise (MAD):  {pre_noise:.4f}")
    print(f"Post-trigger noise (MAD): {post_noise:.4f}")
    print(f"Found {len(peaks)} spikes total "
        f"({(peaks < trigger_idx).sum()} pre, "
        f"{(peaks >= trigger_idx).sum()} post)")

    pre_mask = peaks < trigger_idx
    post_mask = ~pre_mask

    # --- Qt app ---
    app = QtWidgets.QApplication(sys.argv)
    pg.setConfigOptions(antialias=False, useOpenGL=False)  # faster for big data

    win = pg.GraphicsLayoutWidget(title="CC Kistler Spike detection", show=True)
    win.resize(1400, 800)

    # Top: raw signal
    p1 = win.addPlot(row=0, col=0, title="Signal with detected spikes")
    p1.setDownsampling(auto=True, mode='peak')
    p1.setClipToView(True)
    # p1.plot(t, x, pen=pg.mkPen('w', width=1))
    p1.plot(x, pen=pg.mkPen('w', width=1))

    scatter = pg.ScatterPlotItem(
        x=peak_x, y=peak_y,
        pen=pg.mkPen('r', width=2), brush=None,
        symbol='x', size=14,
    )
    p1.addItem(scatter)
    p1.setLabel('bottom', 'Sample index')

    # Bottom: residual + threshold
    p2 = win.addPlot(row=1, col=0, title="Detrended residual")
    p2.setDownsampling(auto=True, mode='peak')
    p2.setClipToView(True)
    # Plot residual at its true x coordinates (offset by `start`)
    #p2.plot(np.arange(len(residual)) + start, residual,
    p2.plot(np.arange(len(residual)), residual,
            pen=pg.mkPen('c', width=1))

    threshold_line = pg.InfiniteLine(
        pos=0.2, angle=0, movable=False,
        pen=pg.mkPen('r', style=QtCore.Qt.PenStyle.DashLine),
    )
    p2.addItem(threshold_line)
    p2.setLabel('bottom', 'Sample index')

    # Link x-axes so zoom/pan are synchronized
    p2.setXLink(p1)

    # trigger_idx = find_trigger(x)
    # print(f"Trigger detected at sample {trigger_idx:,}")

    scatter_pre = pg.ScatterPlotItem(
        x=peaks[pre_mask], y=peak_y[pre_mask],
        pen=pg.mkPen('y', width=2), brush=None,
        symbol='o', size=12,
    )
    scatter_post = pg.ScatterPlotItem(
        x=peaks[post_mask], y=peak_y[post_mask],
        pen=pg.mkPen('r', width=2), brush=None,
        symbol='x', size=14,
    )
    p1.addItem(scatter_pre)
    p1.addItem(scatter_post)

# Mark the trigger
    p1.addItem(pg.InfiniteLine(
        pos=trigger_idx, angle=90,
        pen=pg.mkPen('g', style=QtCore.Qt.PenStyle.DashLine),
        label='trigger',
    ))

    # --3: Peak amplitude of the signal, ignoring noise and spikes
    # -- Option A: Robust max via smoothing
    print("Peak amplitude: Option A")
    # Median filter kills spikes; box filter smooths residual noise
    smooth = uniform_filter1d(
        median_filter(x, size=2001),   # window > spike width
        size=501,                       # extra smoothing for noise
    )
    peak_amp = float(smooth.max())
    peak_idx = int(np.argmax(smooth))
    peak_time = float(t[peak_idx])
    print(f"Peak amplitude: {peak_amp:.4f} V  at t = {1e3*peak_time:.2e} ms "
        f"(sample {peak_idx:,})")
    # Marker on the last pre-trigger spike
    if last_spike is not None:
        p1.addItem(pg.ScatterPlotItem(
            x=[last_spike], y=[x[last_spike]],
            pen=pg.mkPen('b', width=3), brush=None, symbol='o', size=18,
        ))

    # Marker on the peak amplitude
    p1.addItem(pg.ScatterPlotItem(
        x=[peak_idx], y=[peak_amp],
        pen=pg.mkPen('m', width=3), brush=None, symbol='+', size=20,
    ))

    # Horizontal line at the peak amplitude
    p1.addItem(pg.InfiniteLine(pos=peak_amp, angle=0,
                            pen=pg.mkPen('m', style=QtCore.Qt.PenStyle.DotLine)))
    # Option B: High percentile
    # If you'd rather avoid filtering artifacts at the very peak:
    # 99.9th percentile of the spike-free signal
    spike_free = median_filter(x, size=2001)
    peak_amp = float(np.percentile(spike_free, 99.9))
    print(f"Option B: Peak amplitude (99.9th pct, spike-filtered): {peak_amp:.4f}")
    sys.exit(app.exec())



if __name__ == "__main__":
    main()
    
"""
    Tweaks you might need

baseline_window=5001 in the spike detector should be a few times wider than a single spike but well below the spike spacing. If your spikes are ~200 samples wide and ~400k apart, this is fine.

size=2001 in the smoothing for peak amplitude should be wider than the widest spike. If unsure, increase it — the decay is slow so over-smoothing barely affects the peak.

If the first pre-trigger spike (not the last) is what you care about, just use peaks[0] instead of peaks[-1]. Your wording was a bit ambiguous between "find the first spike that exists pre-trigger" (which I interpreted as the one closest to trigger) and "find the earliest spike". Easy to flip either way.
"""
