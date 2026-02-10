import h5py
import numpy as np
import matplotlib.pyplot as plt
import argparse

from read_hdf5 import explore_hdf5, hdf5_file, hdf5_dataset


def plot_hdf5_rhode_schwarz(args):
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
    plt.figure(figsize=(10, 6))
    if len(data.shape) == 1:
        print(f"data.shape[0] {data.shape[0]}")
        plt.plot(
            # time,
            data * kistler_scale,
            color="blue",
        )  # alpha=0.5)
        # plt.legend()
    elif len(data.shape) == 2 and data.shape[0] == 2:  # Time and ch1 data
        print(f"data.shape {data.shape}")
        plt.plot(
            data[0],
            data[1] * kistler_scale,
            color="blue",
        )  # alpha=0.5)
        # plt.title(f"Plot of {dataset_key}")
    plt.ylabel("Delta Pressure / Bar")
    plt.title(f"Plot of {dataset_key}, {exp_id}")
    plt.xlabel("Time / s")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def change_offset_red_pitaya(filename, offset=0.0):
    """ """
    # 'r+': Read/write access without deleting existing data.
    with h5py.File(filename, "r+") as f:
        # dataset_path = "raw-data/red-pitaya-cc"
        dataset_path = "raw-data/cc/kistler/red-pitaya"
        dataset = f[dataset_path]
        dataset.attrs["time_offset"] = offset
        f.close()


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


def plot_hdf5_dataset(filename, dataset_path):
    """
    Plot a dataset from an HDF5 file

    Parameters:
    -----------
    filename : str
        Path to the HDF5 file
    dataset_path : str
       Path to the dataset within the HDF5 file (e.g., '/data' or '/group/dataset')
    """
    data = hdf5_dataset(filename, dataset_path)
    # Create the plot
    plt.figure(figsize=(10, 6))
    if len(data.shape) == 1:
        plt.plot(data)
        plt.xlabel("Index")
    elif len(data.shape) == 2:
        for i in range(min(data.shape[1], 10)):  # Plot up to 10 columns
            plt.plot(data[:, i], label=f"Column {i}")
        plt.xlabel("Index")
        plt.legend()
    plt.ylabel("Value")
    plt.title(f"Plot of {dataset_path}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_hdf5_dataset2(filename, dataset_path, plot_type="line"):
    """
    Plot a dataset from an HDF5 file

    Parameters:
    -----------
    filename : str
        Path to the HDF5 file
    dataset_path : str
        Path to the dataset within the HDF5 file (e.g., '/data' or '/group/dataset')
    plot_type : str
        Type of plot: 'line', 'scatter', 'imshow', or 'auto'
    """
    with h5py.File(filename, "r") as f:
        # Read the dataset
        data = f[dataset_path][:]
        for key, value in mGroup["red-pitaya-cc"].attrs.items():
            print(f"  {key}: {value}")

        # Determine plot type based on data shape
        if plot_type == "auto":
            if len(data.shape) == 1:
                plot_type = "line"
            elif len(data.shape) == 2 and min(data.shape) > 10:
                plot_type = "imshow"
            else:
                plot_type = "line"

        # Create the plot
        plt.figure(figsize=(10, 6))

        if plot_type == "line":
            if len(data.shape) == 1:
                plt.plot(data)
                plt.xlabel("Index")
            elif len(data.shape) == 2:
                for i in range(min(data.shape[1], 10)):  # Plot up to 10 columns
                    plt.plot(data[:, i], label=f"Column {i}")
                plt.xlabel("Index")
                plt.legend()
            plt.ylabel("Value")

        elif plot_type == "scatter":
            if len(data.shape) == 2 and data.shape[1] >= 2:
                plt.scatter(data[:, 0], data[:, 1], alpha=0.5)
                plt.xlabel("Column 0")
                plt.ylabel("Column 1")
            else:
                plt.scatter(range(len(data)), data, alpha=0.5)
                plt.xlabel("Index")
                plt.ylabel("Value")

        elif plot_type == "imshow":
            if len(data.shape) == 2:
                plt.imshow(data, aspect="auto", cmap="viridis")
                plt.colorbar(label="Value")
                plt.xlabel("Column")
                plt.ylabel("Row")
            else:
                print("'imshow' requires 2D data")
                return

        plt.title(f"Plot of {dataset_path}")
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
    if args.offset != 0.0:
        change_offset_red_pitaya(args.file_path, args.offset)
    if args.schwarz:
        plot_hdf5_rhode_schwarz(args)
    elif args.pitaya:
        plot_hdf5_red_pitaya(args)
    else:
        plot_hdf5_dataset(args.file_path, args.dataset_path)

    # plot_hdf5_dataset(filename, "/raw-data/red-pitaya-cc", plot_type="line")
    # Plot a specific dataset (modify the path based on your file structure)
