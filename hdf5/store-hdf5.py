import h5py
import os
from pathlib import Path
import numpy as np
from datetime import datetime
import argparse

H5FILE = "data_with_metadata"


def read_csv_data(args):
    # data = np.genfromtxt(filename, delimiter=" ", dtype='int16')
    data = np.loadtxt(args.file, delimiter=",", max_rows=args.maxrows)
    return data


def read_rs_csv(filepath):
    """
    Read RTB oscilloscope CSV file
    RTB CSV files have metadata header followed by data
    """

    time = []
    voltage = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        # Parse metadata from header
        data_start_line = 0
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Look for metadata (usually key-value pairs or comments)
            if line_stripped.startswith("#") or ":" in line_stripped:
                # Extract metadata
                if ":" in line_stripped:
                    parts = line_stripped.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip("#").strip()
                        value = parts[1].strip()
                        # self.metadata[key] = value

            # Find where data starts (typically has "Time" or numbers)
            if any(
                keyword in line_stripped.lower()
                for keyword in ["in", "time", "x-axis", "channel"]
            ):
                data_start_line = i + 1
                print(f"Found keyword, Starting at line: {data_start_line}")
                break

            # If line starts with a number, probably data
            if (
                line_stripped
                and line_stripped[0].isdigit()
                or line_stripped.startswith("-")
            ):
                data_start_line = i
                break

        # Read data
        print(f"Data starts at line: {data_start_line}")
        for line in lines[data_start_line:]:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    try:
                        time.append(float(parts[0]))
                        voltage.append(float(parts[1]))
                    except ValueError:
                        continue

    return time, voltage
    # return np.array(time, dtype=np.float32), np.array(voltage, dtype=np.float32)


def read_bin_data(filepath):
    # data = np.fromfile(filename, dtype='int16')
    data = np.fromfile(f"{filepath}.bin", dtype="<i2")
    Head = 40
    Foot = 6
    segSize = 16384 + Head + Foot  # 16430
    signal = np.array([], dtype="int16")
    for i in range(0, len(data), segSize):
        segment = data[i : i + segSize]
        signal = np.append(signal, segment[Head:-Foot])
    return data, signal


def create_hdf5(labels, args, filename=H5FILE):
    # Create and write to HDF5 file
    data_dir = Path.cwd()
    file = filename + ".h5"
    file_path = data_dir / file
    try:
        with h5py.File(
            file_path, "w-", driver="sec2"
        ) as f:  # w- Create file, fail if exists
            # Create a dataset and store data
            mgroup = f.create_group("measurements")
            # Multiple intermediate groups can also be created implicitly:
            ccgroup = f.create_group("measurements/cc")
            ccgroup.attrs["description"] = "CC Pressure Kistler Sensor"
            mgroup.create_group("ct")
            mgroup.create_group("st")
            mgroup.create_group("dt")
            ccgroup.create_group("kistler")
            # Store labels in a separate dataset
            """
            label_dataset = f.create_dataset("labels", data=labels.astype("S"))
            label_dataset.attrs["description"] = (
                "Classification labels for each measurement"
            )
            """
            label_dataset = mgroup.create_dataset("labels", data=labels.astype("S"))

            # Add global metadata to the file
            f.attrs["title"] = "Esther ST Experiment Data"
            f.attrs["institution"] = "IPFN-HPL Lab"
            f.attrs["version"] = "1.0"
            # f.attrs["created_date"] = "2025-12-23_17-44-44"  # str(datetime.now())
            # f.attrs["created_date"] = "2025-12-23_17-44-44"  # str(datetime.now())
            f.attrs["shot_date"] = args.shot_date  # "2024-12-26_18-01-03"
            f.attrs["created_date"] = str(datetime.now())
            f.attrs["experiment_id"] = args.experiment_id

        print(f"Data saved to: {file_path}")
        print(f"File size: {file_path.stat().st_size / 1024:.2f} KB")
    except FileExistsError:
        print(
            f"file {file} already exists. Use a different filename or delete the existing file."
        )


def store_hdf5(data, labels, filename=H5FILE):
    # Create and write to HDF5 file
    data_dir = Path.cwd()
    file = filename + ".h5"
    file_path = data_dir / file
    with h5py.File(file_path, "w", driver="sec2") as f:
        # Create a dataset and store data
        mgroup = f.create_group("measurements")
        dataset = mgroup.create_dataset("red-pitaya-cc", data=data, compression="gzip")

        # Add metadata as attributes to the dataset
        dataset.attrs["description"] = "CC Pressure Kistler Sensor"
        # dataset.attrs["units"] = "volt"
        dataset.attrs["units"] = "lsb"
        dataset.attrs["scale"] = 20  # Bar/Volt
        dataset.attrs["channels"] = 1
        dataset.attrs["sampling_rate"] = 125.0e6 / 16  # Hz
        dataset.attrs["time_offset"] = 0.0  # in seconds
        dataset.attrs["file_path"] = str(file_path)
        # dataset.attrs['created_date'] = str(datetime.now())
        # dataset.attrs["sensor_count"] = data.shape[1]
        print(data.shape)

        # Store labels in a separate dataset
        """
        label_dataset = f.create_dataset("labels", data=labels.astype("S"))
        label_dataset.attrs["description"] = (
            "Classification labels for each measurement"
        )
        """
        label_dataset = mgroup.create_dataset("labels", data=labels.astype("S"))

        # Add global metadata to the file
        f.attrs["title"] = "Esther ST Experiment Data"
        f.attrs["institution"] = "IPFN-HPL Lab"
        f.attrs["version"] = "1.0"
        # f.attrs["created_date"] = "2025-12-23_17-44-44"  # str(datetime.now())
        # f.attrs["created_date"] = "2025-12-23_17-44-44"  # str(datetime.now())
        f.attrs["created_date"] = str(datetime.now())
        f.attrs["experiment_id"] = "S-116"

    print(f"Data saved to: {file_path}")
    print(f"File size: {file_path.stat().st_size / 1024:.2f} KB")


def update_red_hdf5(args, hd5filename="data_with_metadata"):
    #  Update HDF file with R&S csv data
    # data, signal = read_bin_data(rpfilename)
    time, signal = read_rs_csv(args.file_path)
    data = np.array(signal, dtype=np.int16)
    data_dir = Path.cwd()
    file = hd5filename + ".h5"
    file_path = data_dir / file
    with h5py.File(file_path, "a") as f:
        if "measurements" not in f:
            print("✗ 'measurements' groups not exist, skipping")
            return
        kGroup = f["measurements/cc/kistler"]
        print(list(kGroup.keys()))
        dataset = kGroup.create_dataset("red-pitaya", data=data, compression="gzip")

        # Add metadata as attributes to the dataset
        dataset.attrs["description"] = "CC Pressure Kistler Sensor red-pitaya data"
        # dataset.attrs["units"] = "volt"
        dataset.attrs["units"] = "lsb"
        dataset.attrs["scale"] = args.kistler_scale  # Bar/Volt
        dataset.attrs["channels"] = 1
        dataset.attrs["sampling_rate"] = 125.0e6 / 16  # Hz
        dataset.attrs["time_offset"] = 0.0  # in seconds
        dataset.attrs["file_path"] = str(file_path)
        # print(signal.shape)


def update_rs_hdf5(csvfilename, hd5filename="data_with_metadata"):
    t, data = read_rs_csv(csvfilename)
    time = np.array(t, dtype=np.float32)
    signal = np.array(data, dtype=np.float32)
    #  Update HDF file with R&S csv data
    data_dir = Path.cwd()
    file = hd5filename + ".h5"
    file_path = data_dir / file
    with h5py.File(file_path, "a") as f:
        if "measurements" not in f:
            print("✗ 'measurements' groups not exist, skipping")
            return
        mGroup = f["measurements"]
        print(list(mGroup.keys()))
        if "time" not in mGroup:
            dataset = mGroup.create_dataset("time", data=time, compression="gzip")
            dataset.attrs["description"] = "Rhode-schwarz Control Room"
            # dataset.attrs["units"] = "volt"
            dataset.attrs["units"] = "second"
        if "rhode-schwarz-cc" not in mGroup:
            dataset = mGroup.create_dataset(
                "rhode-schwarz-cc", data=signal, compression="gzip"
            )
            dataset.attrs["description"] = "CC Pressure Kistler Sensor"
            # dataset.attrs["units"] = "volt"
            dataset.attrs["units"] = "volt"
            dataset.attrs["scale"] = 20  # Bar/Volt
            dataset.attrs["channels"] = 1
            # dataset.attrs["file_path"] = str(file_path)
            # dataset.attrs["sampling_rate"] = 125.0e6 / 16  # Hz
            # dataset.attrs["created_date"] = "2025-12-23_17-44-44"  # str(datetime.now())

        else:
            print("✗ 'rhode-schwarz-cc' dataset already exists, skipping")
        # Create a dataset and store data in group

    print(f"Data saved to: {file_path}")
    print(f"File size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to save binary Esther Shot data in HDF5 files"
    )
    parser.add_argument(
        "-p", "--pitaya", action="store_true", help="Update with RedPitaya "
    )
    parser.add_argument(
        "-s", "--schwarz", action="store_true", help="Update with Rhode-Schwarz CSV"
    )
    parser.add_argument(
        "-f", "--file_path", type=str, help="File to read", default="dataXX"
    )
    parser.add_argument(
        "-e", "--experiment_id", type=str, help="Experiment Id", default="S_117"
    )
    parser.add_argument(
        "-d", "--shot_date", type=str, help="Shot date", default="2024-12-26_18-01-03"
    )
    parser.add_argument(
        "-k", "--kistler_scale", type=float, help="Kistler scale", default="20.0"
    )
    """
    parser.add_argument(
        "-m",
        "--maxrows",
        type=int,
        help="The maximum number of rows to read.",
        default="1000000",
    )
    parser.add_argument(
        "-d", "--decim", type=int, help="Plot decimation", default="100"
    )
    """
    args = parser.parse_args()

    if args.schwarz:
        # update_hdf5(args.file_pathtime, ch1_signal)
        update_rs_hdf5(args.file_path)
    elif args.pitaya:
        update_red_hdf5(args)
    else:
        # data, signal = read_bin_data(args.file_path)
        # print(f"RP file read. Data len: {len(signal)}")
        dirname, basename = os.path.split(args.file_path)
        # Create sample data
        labels = np.array(["class_A", "class_B", "class_C"] * 33 + ["class_A"])
        create_hdf5(labels, args)
        # store_hdf5(data, labels)
