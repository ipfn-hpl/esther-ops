import h5py
import numpy as np
import matplotlib.pyplot as plt
import argparse

from read_hdf5 import explore_hdf5, hdf5_file, hdf5_dataset
from EstherHDF5Handler import EstherHDF5Handler


def plot_kistler(estherHdf5):
    """Get metadata about a dataset."""
    fill_pressure = estherHdf5.get_attr("fill_pressure", "experiment")
    print(f"fill_pressure: {fill_pressure} Bar")
    kistler_range = estherHdf5.get_attr("range", "raw-data/cc/kistler")
    kistler_scale = kistler_range / 10.0  # Bar per Volt
    rp_key = "raw-data/cc/kistler/red-pitaya"
    print(f"Dict: {estherHdf5.get_dataset_info(rp_key))}")
    #
    fig = plt.figure()
    gs = fig.add_gridspec(2, hspace=0)
    axs = gs.subplots(sharex=True)
    fig.suptitle("Kistler Data")
    rs_key = "raw-data/cc/kistler/rohde-schwarz"
    data = estherHdf5.get_dataset(rs_key)
    axs[0].plot(
        data[0],
        data[1] * kistler_scale + fill_pressure,
        color="blue",
    )  # alpha=0.5)
    axs[0].set_ylabel("Pressure / Bar")
    data = estherHdf5.get_dataset(rp_key)
    sampling_rate = estherHdf5.get_attr("sampling_rate", rp_key)
    decimation = estherHdf5.get_attr("decimation", rp_key)
    time_offset = estherHdf5.get_attr("time_offset", rp_key)
    yrange = 2**13
    print(f"data.shape[0] {data.shape[0]}")
    time = np.arange(data.shape[0]) / (sampling_rate/decimation) + time_offset
    axs[1].plot(
        time,
        data / yrange,
        color="red",  # linewidth=2)
    )  # alpha=0.5)
    plt.show()


# Example usage
if __name__ == "__main__":
    # Replace with your HDF5 file path
    # filename = "data_with_metadata.h5"
    parser = argparse.ArgumentParser(
        description="Script to plot dataset Shot data in HDF5 files"
    )
    parser.add_argument(
        "-f",
        "--file_path",
        type=str,
        help="File to read",
        default="data_with_metadata.h5",
    )
    parser.add_argument(
        "-d",
        "--dataset_path",
        type=str,
        help="Dataset plot to plot",
        default="/raw-data/rohde-schwarz-cc",
    )
    parser.add_argument("-e", "--explore", action="store_true", help="Explore hdf5")
    parser.add_argument("-p", "--pitaya", action="store_true", help="Plot RedPitaya ")
    parser.add_argument(
        "-s", "--schwarz", action="store_true", help="Plot with rohde-Schwarz CSV"
    )
    parser.add_argument(
        "-m",
        "--maxrows",
        type=int,
        help="The maximum number of rows to plot.",
        default="1000000",
    )
    parser.add_argument(
        "-o",
        "--offset",
        type=float,
        help="The time offset of the RedPitaya data.",
        default=0.0,
    )
    # parser.add_argument(
    #    "-d", "--decim", type=int, help="Plot decimation", default="100"
    # )
    args = parser.parse_args()

    # First, explore the structure
    try:
        with EstherHDF5Handler(args.file_path, mode="r") as h5:
            print("Contents:")
            for item in h5.list_contents():
                print(f"  {item}")

            all_attributes = h5.list_all_attrs()

            for path, attrs in all_attributes.items():
                print(f"\n{path}:")
                for key, value in attrs.items():
                    print(f"  {key}: {value}")
            plot_kistler(h5)
        # explore_hdf5(args.file_path)
    except FileNotFoundError:
        print(
            f"File '{args.file_path}' not found. Please provide a valid HDF5 file path."
        )
