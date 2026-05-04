import argparse

import numpy as np
import matplotlib.pyplot as plt
import h5py
import sys
from pathlib import Path


def get_attr(hdf, path: str = "/", key: str = "") -> any:
    """get a single attribute value."""
    obj = hdf if path == "/" else hdf[path]
    return obj.attrs[key]


def plot_kistler(hdf):
    fig = plt.figure()
    gs = fig.add_gridspec(2, hspace=0.1)
    axs = gs.subplots(sharex=True)
    key = ""
    try:
        exp = hdf["experiment"]
        attrs = dict(exp.attrs)  # h5.get_attrs("diagnostics/experimental-hall/cc")
        key = "cc_fill_pressure"
        fill_pressure = attrs[key]
        date = attrs["date"]

        print(f"fill_pressure: {fill_pressure} Bar, date {date}")
        diag = hdf["diagnostics/experimental-hall/cc/kistler"]
        attrs = dict(diag.attrs)  # h5.get_attrs("diagnostics/experimental-hall/cc")
        key = "pressure_range"
        kistler_range = attrs[key]
        kistler_scale = kistler_range / 10.0  # Bar per Volt
        print(f"Attributes: {attrs}")
        rtime = hdf["raw-data/control-room/rohde-schwarz/waveforms/TIME"][:]
        rdata = hdf["raw-data/control-room/rohde-schwarz/waveforms/C1"][:]
        print(rdata.shape)
        # r_data = estherHdf5.get_rohde_schwarz_data()
        index = np.argmax(rdata)
        timeMaxRS = rtime[index]
        print(f" schwarz max index {index}, time: {timeMaxRS}")
        axs[0].set_title("Rohde-Schwarz Oscilloscope", fontsize="small", loc="right")
        axs[0].plot(
            rtime,
            rdata * kistler_scale + fill_pressure,
            color="blue",
        )  # alpha=0.5)
        axs[0].set_ylabel("Pressure / Bar")
        axs[0].grid()
        #

        red = hdf["raw-data/control-room/red-pitaya/metadata"]
        attrs = dict(red.attrs)  # h5.get_attrs("diagnostics/experimental-hall/cc")
        print(f"Red Attributes: {attrs}")
        key = "sample_rate"
        sample_rate = get_attr(hdf, "raw-data/control-room/red-pitaya/metadata", key)
        key = "decimation"
        decimation = get_attr(hdf, "raw-data/control-room/red-pitaya/metadata", key)

        key = "raw-data/control-room/red-pitaya/waveforms/ch1"
        pdata = hdf[key][:]

        print(f"Data shape: {pdata.shape}, sample_rate: {sample_rate} Hz")
        time = np.arange(pdata.shape[0]) / sample_rate * decimation  # time_offset
        index = np.argmax(pdata)
        timeMaxRP = time[index]
        print(f"pitaya max index {index}, time: {timeMaxRP}")
        timeOffSet = timeMaxRS - timeMaxRP
        print(f"pitaya TimeOffset  {timeOffSet} ms ")
        axs[1].plot(
            time,
            pdata,
            color="red",
        )  # alpha=0.5)
        axs[1].set_title("Red Pitaya ADC Ch1", fontsize="small", loc="right")
        axs[1].grid()
    except KeyError:
        print(f"object '{key}' doesn't exist in dataset")
    fig.supxlabel("Time / ms")
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Script to plot dataset Shot data stored in HDF5 files"
    )
    parser.add_argument("-a", "--afs", action="store_true", help="Read from AFS")
    # parser.add_argument("-e", "--explore", action="store_true", help="Explore hdf5")

    parser.add_argument(
        "-f",
        "--file_h5",
        type=str,
        help="File to read",
        default="data_with_metadata.h5",
    )
    parser.add_argument(
        "-o",
        "--offset",
        type=float,
        help="The time offset of the RedPitaya data.",
        default=1.0e27,
    )
    args = parser.parse_args()
    path_h5 = Path(args.file_h5)
    if not path_h5.exists():
        print(f"Error: File '{args.file_h5}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.offset != 1.0e27:
        # 'r+': Read/write access without deleting existing data.
        with h5py.File(path_h5, "r+") as h5:
            sys.exit(1)
    with h5py.File(path_h5, "r") as h5:
        # temp_data = h5["raw-data/control-room/rohde-schwarz/waveforms/C1"][:]
        print(f"Type of h5: {type(h5)}")
        plot_kistler(h5)


if __name__ == "__main__":
    main()
