import h5py
import os
from pathlib import Path
import numpy as np
from datetime import datetime
import argparse


def explore_hdf5(filename):
    """Print the structure of an HDF5 file"""

    def print_structure(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"Dataset: {name}, Shape: {obj.shape}, Dtype: {obj.dtype}")
        elif isinstance(obj, h5py.Group):
            print(f"Group: {name}")

    with h5py.File(filename, "r") as f:
        print(f"Structure of {filename}:")
        f.visititems(print_structure)
        print()


def hdf5_file(filename):
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
    return h5py.File(filename, "r")


def hdf5_dataset(filename, dataset_path):
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
    data = []
    with h5py.File(filename, "r") as f:
        # Read the dataset
        data = f[dataset_path][:]

    return data


#                 plot_type = "line"
def read_hdf5(file_path):
    with h5py.File(file_path, "r") as f:
        print("\n=== File-level Metadata ===")
        for key, value in f.attrs.items():
            print(f"{key}: {value}")

        print("\n=== Keys in file ===")
        print(list(f.keys()))

        print("\n--- All Datasets and Groups ---")

        def print_structure(name, obj):
            if isinstance(obj, h5py.Dataset):
                print(f"  Dataset: {name} | Shape: {obj.shape} | Type: {obj.dtype}")
            elif isinstance(obj, h5py.Group):
                print(f"  Group: {name}")

        f.visititems(print_structure)

        print("\n=== Datasets in group measurements ===")
        mGroup = f["measurements"]
        print(list(mGroup.keys()))

        print("\n=== Dataset: measurements ===")
        # measurements = f["measurements"][:]
        rPcc = mGroup["red-pitaya-cc"][:]
        print(f"Shape: {rPcc.shape}")
        print(f"Data type: {rPcc.dtype}")

        print("\nMetadata (attributes):")
        for key, value in mGroup["red-pitaya-cc"].attrs.items():
            print(f"  {key}: {value}")
        return mGroup


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to save binary Shot data in HDF5 files"
    )
    parser.add_argument("-c", "--csv", action="store_true", help="Open CSV")
    parser.add_argument("-e", "--explore", action="store_true", help="Explore hdf")
    parser.add_argument(
        "-f", "--file_path", type=str, help="File to read", default="dataXX.bin"
    )
    parser.add_argument(
        "-m",
        "--maxrows",
        type=int,
        help="The maximum number of rows to read.",
        default="1000000",
    )
    # parser.add_argument(
    #    "-d", "--decim", type=int, help="Plot decimation", default="100"
    # )
    args = parser.parse_args()
    filename = "data_with_metadata"
    data_dir = Path.cwd()
    file = filename + ".h5"
    file_path = data_dir / file
    if args.explore:
        explore_hdf5(file_path)
    else:
        read_hdf5(file_path)
