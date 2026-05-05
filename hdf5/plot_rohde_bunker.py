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
        key = "raw-data/experimental-hall/rohde-schwarz/waveforms/TIME"
        rtime = hdf[key][:]
        key = "raw-data/experimental-hall/rohde-schwarz/waveforms/C1"
        rdata = hdf[key][:]
        print(rdata.shape)
        # r_data = estherHdf5.get_rohde_schwarz_data()
        index = np.argmax(rdata)
        timeMaxRS = rtime[index]
        print(f" schwarz max index {index}, time: {timeMaxRS}")
        axs[0].set_title(
            "Bunker Rohde-Schwarz Oscilloscope", fontsize="small", loc="right"
        )
        axs[0].plot(
            rtime,
            rdata * kistler_scale + fill_pressure,
            color="blue",
            label="Kistler CC",
        )  # alpha=0.5)
        # axs[0].set_ylabel("Pressure / Bar")
        key = "raw-data/experimental-hall/rohde-schwarz/waveforms/C2"
        rdata = hdf[key][:]
        # r_data = estherHdf5.get_rohde_schwarz_data()
        axs[0].plot(
            rtime,
            rdata,  # * kistler_scale + fill_pressure,
            color="red",
            label="Kistler CT",
        )  # alpha=0.5)
        # axs[0].set_ylabel("Pressure / Bar")
        axs[0].grid()
        axs[0].legend(loc="upper right")
        #

        key = "raw-data/experimental-hall/rohde-schwarz/waveforms/C3"
        rdata = hdf[key][:]
        axs[1].plot(
            rtime,
            rdata,  # * kistler_scale + fill_pressure,
            color="blue",
            label="Thorlabs ST1",
        )
        key = "raw-data/experimental-hall/rohde-schwarz/waveforms/C4"
        rdata = hdf[key][:]
        axs[1].plot(
            rtime,
            rdata,  # * kistler_scale + fill_pressure,
            color="red",
            label="Dumptank",
        )
        axs[1].grid()
        axs[1].legend(loc="upper left")
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
            rkey = "raw-data/control-room/red-pitaya/metadata"
            dataset = h5[rkey]
            dataset.attrs["time_offset"] = args.offset
            sys.exit(1)
    with h5py.File(path_h5, "r") as h5:
        # temp_data = h5["raw-data/control-room/rohde-schwarz/waveforms/C1"][:]
        print(f"Type of h5: {type(h5)}")
        plot_kistler(h5)


if __name__ == "__main__":
    main()
