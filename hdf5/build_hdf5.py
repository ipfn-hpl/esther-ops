"""
Here's a Python class for import data in EstherHDF5Handler:

https://github.com/ipfn-hpl/esther-ops/tree/main/hdf5

python3 build_hdf5.py -i -e "S-116" -d "2025-12-23_17-44-44" -k 200
python3 build_hdf5.py --schwarz -f ~/Documents/Data-files/RS_ControlRoom/S_116/WFM03.CSV
python3 build_hdf5.py --pitaya -f ../red-pitaya/data-files/S_116/data_file_2025-12-23_17-44-44.csv
"""

import numpy as np
from datetime import datetime
from EstherHDF5Handler import EstherHDF5Handler
import argparse

H5FILE = "data_with_metadata.h5"


def read_csv(filepath):
    """
    Read RTB oscilloscope/Red pitaya CSV file
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


def import_hdf5_red(filename, args):
    #  Update HDF file with Red pitaya csv data
    try:
        t, ch1 = read_csv(args.file_path)
    except FileNotFoundError:
        print(f" File: {args.file_path}  not found, existing")
        return

    data = np.array(ch1, dtype=np.int16)
    with EstherHDF5Handler(filename, mode="a") as h5:
        h5.create_dataset(
            "raw-data/cc/kistler/red-pitaya",
            data=data,
            attrs={
                "unit": "lsb",
                "channels": 1,
                "has_time": False,
                "sampling_rate": 125.0e6,  # Hz
                "decimation": 16,
                "time_offset": args.time_offset,
                # "sensor_id": 42,
            },
            compression="gzip",
        )


def import_hdf5_schwarz(filename, args):
    try:
        t, ch1 = read_csv(args.file_path)
    except FileNotFoundError:
        print(f" File: {args.file_path}  not found, existing")
        return
    data = np.array([t, ch1], dtype=np.float32)
    #  Update HDF file with R&S csv data
    with EstherHDF5Handler(filename, mode="a") as h5:
        h5.create_dataset(
            "raw-data/cc/kistler/rhode-schwarz",
            data=data,
            attrs={
                "unit": "volt",
                "channels": 1,
                "has_time": True,
            },
            compression="gzip",
        )


# def import_hdf5_schwarz(filename, csvfilename):
#  Update HDF file with R&S csv data
# with EstherHDF5Handler(filename, mode="a") as h5:


def init_hdf5(filename, args):
    with EstherHDF5Handler(filename, mode="w-") as h5:
        h5.import_from_dict(
            {
                "@title": "Esther ST Experiment Data",
                "@institution": "IPFN-HPL Lab",
                "@created_date": str(datetime.now()),
                # "@institution" = ""
                "@version": "1.0",
                "@author": "Bernardo",
                "experiment": {
                    "@date": args.shot_date,
                    "@name": args.experiment_name,
                    "@fill_pressure": args.fill_pressure,  # Bar
                    "readings": [1.0, 2.0, 3.0, 4.0],
                },
                "raw-data": {
                    "@description": "Raw Data from instruments in binary",
                    "cc": {
                        "@description": "Combustion Chamber",
                        "kistler": {
                            "@description": "CC Pressure Kistler Sensor",
                            "@range": args.kistler_range,  # Bar
                        },
                    },
                    "ct": {
                        "@description": "Compression Tube Section",
                    },
                    "st": {
                        "@description": "Shock Tube Section",
                    },
                    "dt": {
                        "@description": "Dump Tank Section",
                    },
                    # "readings": [1.0, 2.0, 3.0, 4.0],
                },
                "cal-data": {},
            }
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to save binary Shot data in HDF5 files"
    )
    # parser.add_argument("-c", "--csv", action="store_true", help="Open CSV")
    parser.add_argument("-x", "--explore", action="store_true", help="Explore hdf")
    parser.add_argument("-i", "--init", action="store_true", help="Init hdf")
    parser.add_argument(
        "-f", "--file_path", type=str, help="File to read", default="dataXX.bin"
    )
    parser.add_argument(
        "-p", "--pitaya", action="store_true", help="Update with RedPitaya "
    )
    parser.add_argument(
        "-s", "--schwarz", action="store_true", help="Update with Rhode-Schwarz CSV"
    )
    parser.add_argument(
        "-e", "--experiment_name", type=str, help="Experiment Name", default="S-117"
    )
    parser.add_argument(
        "-d", "--shot_date", type=str, help="Shot date", default="2024-12-26_18-01-03"
    )
    parser.add_argument(
        "-k", "--kistler_range", type=float, help="Kistler Range (Bar)", default="200.0"
    )
    parser.add_argument(
        "-l",
        "--fill_pressure",
        type=float,
        help="CC Fill Pressure (Bar)",
        default="40.0",
    )
    parser.add_argument(
        "-t",
        "--time_offset",
        type=float,
        help="RedPitaya time Offset to R&S",
        default="0.0",
    )
    args = parser.parse_args()
    filename = H5FILE
    # data_dir = Path.cwd()
    # file = filename + ".h5"
    # file_path = data_dir / file
    if args.explore:
        with EstherHDF5Handler(filename, mode="r") as h5:
            print("Contents:")
            for item in h5.list_contents():
                print(f"  {item}")

            all_attributes = h5.list_all_attrs()

            for path, attrs in all_attributes.items():
                print(f"\n{path}:")
                for key, value in attrs.items():
                    print(f"  {key}: {value}")
            # explore_hdf5(file_path)
    elif args.init:
        init_hdf5(filename, args)
    if args.pitaya:
        print("pitaya:")
        import_hdf5_red(filename, args)
    elif args.schwarz:
        # update_hdf5(args.file_pathtime, ch1_signal)
        import_hdf5_schwarz(filename, args)
