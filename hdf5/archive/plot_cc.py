import h5py
import numpy as np
import matplotlib.pyplot as plt
import argparse

from read_hdf5 import explore_hdf5, hdf5_file, hdf5_dataset


def plot_both(args):
    """
    Plot a dataset from an HDF5 file

    Parameters:
    -----------
    args : args
    """
    f = hdf5_file(args.file_path)
    exp_id = f.attrs["experiment_name"]
    print("")
    print(f"HDF5 File '{f}' ({exp_id}) attributes:")
    for key, value in f.attrs.items():
        print(f"  {key}: {value}")

    # dataset_path = "raw-data/time"
    kGroup = f["raw-data/cc/kistler"]
    print(f"Group Keys {kGroup}:")
    print(list(kGroup.keys()))
    kistler_range = kGroup.attrs["range"]
    kistler_scale = kistler_range / 10.0  # Bar per Volt

    fill_pressure = kGroup.attrs["fill_pressure"]
    print(f"fill_pressure: {fill_pressure} Bar")
    dataset_key = "rhode-schwarz"
    # dataset_path = "raw-data/cc/kistler/rhode-schwarz"
    try:
        dataset = kGroup[dataset_key]
    except KeyError:
        print(f"object '{dataset_key}' doesn't exist")
        return
    print("")
    print(f"Dataset '{dataset_key}' attributes:")
    for key, value in dataset.attrs.items():
        print(f"  {key}: {value}")
    data = dataset[:]
    # plt.figure(figsize=(10, 6))
    fig = plt.figure()
    gs = fig.add_gridspec(2, hspace=0)
    axs = gs.subplots(sharex=True)
    fig.suptitle("kistler Data")
    """
    if len(data.shape) == 1:
        print(f"data.shape[0] {data.shape[0]}")
        axs[0].plot(
            # time,
            data * kistler_scale + fill_pressure,
            color="cyan",  # linewidth=2
        )  # alpha=0.5)
        # plt.legend()
    elif len(data.shape) == 2 and data.shape[0] == 2:  # Time and ch1 data
    """
    print(f"data.shape {data.shape}")
    axs[0].plot(
        data[0],
        data[1] * kistler_scale + fill_pressure,
        color="blue",
    )  # alpha=0.5)
    # plt.title(f"Plot of {dataset_key}")
    axs[0].set_ylabel("Pressure / Bar")
    dataset_key = "red-pitaya"
    # dataset_path = "raw-data/cc/kistler/rhode-schwarz"
    try:
        dataset = kGroup[dataset_key]
    except KeyError:
        print(f"object '{dataset_key}' doesn't exist")
        return
    print("")
    print(f"Dataset '{dataset_key}' attributes:")
    for key, value in dataset.attrs.items():
        print(f"  {key}: {value}")
    sampling_rate = dataset.attrs["sampling_rate"]
    time_offset = dataset.attrs["time_offset"]
    print(f"  sampling_rate: {sampling_rate}")
    data = dataset[:]
    yrange = 2**13
    print(f"data.shape[0] {data.shape[0]}")
    time = np.arange(data.shape[0]) / sampling_rate + time_offset
    axs[1].plot(
        time,
        data / yrange,
        color="red",  # linewidth=2)
    )  # alpha=0.5)
    # plt.scatter(time, data / yrange, alpha=0.5)
    # plt.title(f"Plot of {dataset_key}, {exp_id}")
    # plt.xlabel("Time / s")
    # plt.grid(True, alpha=0.3)
    # plt.tight_layout()
    plt.show()


def plot_hdf5_red_pitaya(args):
    """
    Plot a dataset from an HDF5 file

    Parameters:
    -----------
    filename : str
    """
    f = hdf5_file(args.file_path)
    exp_id = f.attrs["experiment_name"]
    print("")
    print(f"HDF5 File '{f}' ({exp_id}) attributes:")
    for key, value in f.attrs.items():
        print(f"  {key}: {value}")
    kGroup = f["raw-data/cc/kistler"]
    # kistler_scale = kGroup.attrs["scale"]
    print(f"Group Keys {kGroup}:")
    print(list(kGroup.keys()))
    dataset_key = "red-pitaya"
    # dataset_path = "raw-data/cc/kistler/rhode-schwarz"
    try:
        dataset = kGroup[dataset_key]
    except KeyError:
        print(f"object '{dataset_key}' doesn't exist")
        return
    print("")
    print(f"Dataset '{dataset_key}' attributes:")
    for key, value in dataset.attrs.items():
        print(f"  {key}: {value}")
    sampling_rate = dataset.attrs["sampling_rate"]
    time_offset = dataset.attrs["time_offset"]
    print(f"  sampling_rate: {sampling_rate}")
    data = dataset[:]
    yrange = 2**13
    if len(data.shape) == 1:
        print(f"data.shape[0] {data.shape[0]}")
        time = np.arange(data.shape[0]) / sampling_rate + time_offset
        plt.figure(figsize=(10, 6))
        plt.plot(
            time,
            data / yrange,
            color="red",  # linewidth=2)
        )  # alpha=0.5)
        # plt.scatter(time, data / yrange, alpha=0.5)
        plt.xlabel("Time / s")
        # plt.legend()
        plt.ylabel("Value")
        plt.title(f"Plot of {dataset_key}, {exp_id}")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
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
        default="/raw-data/rhode-schwarz-cc",
    )
    parser.add_argument("-e", "--explore", action="store_true", help="Explore hdf5")
    parser.add_argument("-p", "--pitaya", action="store_true", help="Plot RedPitaya ")
    parser.add_argument(
        "-s", "--schwarz", action="store_true", help="Plot with Rhode-Schwarz CSV"
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
        explore_hdf5(args.file_path)
    except FileNotFoundError:
        print(
            f"File '{args.file_path}' not found. Please provide a valid HDF5 file path."
        )
    if args.schwarz:
        plot_both(args)
    elif args.pitaya:
        plot_hdf5_red_pitaya(args)

    # plot_hdf5_dataset(filename, "/raw-data/red-pitaya-cc", plot_type="line")
    # Plot a specific dataset (modify the path based on your file structure)
