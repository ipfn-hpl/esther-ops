"""
Here's a Python class for import data in EstherHDF5Handler:

https://github.com/ipfn-hpl/esther-ops/tree/main/hdf5

python3 build_hdf5.py -i -e "S-116" -d "2025-12-23_17-44-44" -k 200
python3 build_hdf5.py --schwarz -f ~/Documents/Data-files/RS_ControlRoom/S_116/WFM03.CSV
python3 build_hdf5.py --pitaya -f ../red-pitaya/data-files/S_116/data_file_2025-12-23_17-44-44.csv
"""

import argparse
import sys
import numpy as np
import pandas as pd
import h5py
from datetime import datetime
from EstherHDF5Handler import EstherHDF5Handler
from parse_csv import parse_tektronix_csv
from pathlib import Path

H5FILE_PATH = "data_with_metadata.h5"


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


def import_hdf5_rohde(args, group: str = "raw-data/experimental-hall/rohde-schwarz/"):
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: File '{args.csv_file}' not found.", file=sys.stderr)
        return
    # column_info = parse_rohde_csv(csv_path)
    column_info = []
    # Read CSV - pandas handles scientific notation automatically
    df = pd.read_csv(csv_path)
    # with open(csv_path, "r", newline="") as f:
    # Parse column names to extract units (e.g., "C1 in V" -> name="C1", unit="V")
    for col in df.columns:
        if " in " in col:
            name, unit = col.rsplit(" in ", 1)
            column_info.append(
                {"original": col, "name": name.strip(), "unit": unit.strip()}
            )
        else:
            column_info.append({"original": col, "name": col, "unit": ""})
    print(f"R Column I: {column_info}")
    with h5py.File(H5FILE_PATH, "a") as hf:
        try:
            data_grp = hf.create_group(group + "waveforms")
        except ValueError:
            print(" Unable to create group (name already exists)")
            key = group + "waveforms"
            data_grp = hf[key]
        for info in column_info:
            print(f"Column O: {info['original']}, N:  {info['name']}")
            data = df[info["original"]].values.astype(np.float32)
            name = info["name"]
            if name == "in s":
                name = "TIME"
            ds = data_grp.create_dataset(
                name, data=data, compression="gzip", compression_opts=4
            )
            # Store unit as attribute
            if info["unit"]:
                ds.attrs["unit"] = info["unit"]
        # Store metadata
        data_grp.attrs["source_file"] = csv_path.name
        data_grp.attrs["num_samples"] = len(df)
        data_grp.attrs["columns"] = [info["name"] for info in column_info]


def import_hdf5_tektronix(args, group: str = "raw-data/experimental-hall/tektronix/"):
    if not Path(args.csv_file).exists():
        print(f"Error: File '{args.csv_file}' not found.", file=sys.stderr)
        return
    metadata, df = parse_tektronix_csv(args.csv_file)
    columns = metadata.pop("_columns")
    print(f" Tektronix CVS Columns: {columns}")
    h_unit = metadata.get("Horizontal Units", "s")
    v_units = metadata.get("Vertical Units", [])
    if isinstance(v_units, str):
        v_units = [v_units]

    column_info = []
    channel_idx = 0
    for col in columns:
        if col.upper() == "TIME":
            column_info.append({"original": col, "name": "TIME", "unit": h_unit})
        else:
            unit = v_units[channel_idx] if channel_idx < len(v_units) else "V"
            column_info.append({"original": col, "name": col, "unit": unit})
            channel_idx += 1
    with h5py.File(H5FILE_PATH, "a") as hf:
        # with EstherHDF5Handler(H5FILE, mode="a") as h5:
        # Store waveform data
        data_grp = hf.create_group(group + "waveforms")
        for info in column_info:
            data = df[info["original"]].values.astype(np.float32)
            ds = data_grp.create_dataset(
                info["name"], data=data, compression="gzip", compression_opts=4
            )
            if info["unit"]:
                ds.attrs["unit"] = info["unit"]


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
            "raw-data/cc/kistler/rohde-schwarz",
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
    try:
        with EstherHDF5Handler(filename, mode="w-") as h5:
            h5.import_from_dict(
                {
                    "header": {
                        "@title": "Esther ST Experiment Data",
                        "@institution": "IPFN-HPL Lab",
                        "@created_date": str(datetime.now()),
                        "@version": "1.0",
                        "@author": "bernardo.carvalho@tecnico.ulisboa.pt",
                    },
                    "experiment": {
                        "@date": args.shot_date,
                        "@name": args.experiment_name,
                        "@cc_fill_pressure": args.fill_pressure,  # Bar
                        "@he_h2_o2_ratios": [8.0, 2.0, 1.2],
                    },
                    "diagnostics": {
                        "@description": "Sensors/instruments",
                        "control-room": {
                            "@description": "Sensors in HPL Control room",
                        },
                        "experimental-hall": {
                            "@description": "Sensors/instruments in HPL experimental hall",
                            "cc": {
                                "@description": "Combustion Chamber",
                                "kistler": {
                                    "@description": "CC Pressure Kistler Sensor",
                                    "@amplifier": "Kistler Type 5015",
                                    "@wire_number": "504",
                                    "@pressure_range": args.kistler_range,  # Bar
                                    "@data_key_0": "raw-data/control-room/rohde-schwarz",
                                    "@data_key_0": "raw-data/control-room/red-pitaya",
                                },
                            },
                            "ct": {
                                "@description": "Compression Tube Section",
                                "kistler": {
                                    "@description": "CC Pressure Kistler Sensor",
                                    "@amplifier": "Kistler Type 5015",
                                    "@wire_number": "501",
                                    "@pressure_range": 10,  # Bar
                                    "@data_key_0": "raw-data/experimental-hall/rohde-schwarz",
                                    "@data_key_1": "raw-data/experimental-hall/tektronix/waveforms/CH1",
                                },
                            },
                            "st": {
                                "@description": "Shock Tube Section",
                            },
                            "dt": {
                                "@description": "Dump Tank Section",
                            },
                        },
                    },
                    "raw-data": {
                        "@description": "Raw Data from instruments in binary",
                        "control-room": {
                            "@description": "Instruments in HPL Control room",
                            "rohde-schwarz": {
                                "metadata": {
                                    "@model": "rtb2004",
                                    "@serial_number": "1333.1005k04/107554",
                                    "@firmware_version": "02.400",
                                    "@has_time": True,
                                    "@sample_interval": 2e-10,
                                    #                                    "@num_samples": 2e1,
                                    "@channels": 1,
                                    "@unit": "V",
                                    "@vertical_scale": "Volt",
                                },
                            },
                            "red-pitaya": {
                                "metadata": {
                                    "@model": "STEMlab 125-14",
                                    "@hostname": "rp-f01735.local",
                                    "@ecosystem": "1.04-93661995d",
                                    "@has_time": False,
                                    "@sample_rate": 125.0e6,  # Hz
                                    "@decimation": 16,
                                    "@channels": 1,
                                    "@unit": "lsb",
                                    "@vertical_range": "+-1V",
                                },
                            },
                        },
                        "experimental-hall": {
                            "@description": "Instruments in HPL experimental hall",
                            "rohde-schwarz": {
                                "metadata": {
                                    "@model": "rtb2004",
                                    "@serial_number": "1333.1005k04/207766",
                                    "@firmware_version": "02.400",
                                    "@has_time": True,
                                    #                                    "@sample_interval": 2e-10,
                                    #                                    "@num_samples": 2e1,
                                    #                                    "@channels": 4,
                                    "@unit": "V",
                                    "@vertical_scale": "Volt",
                                },
                            },
                            "tektronix": {
                                "metadata": {
                                    "@model": "MDO4104B-3",
                                    "@serial_number": "C020372",
                                    "@firmware_version": "3.18",
                                    "@has_time": True,
                                    "@sample_interval": 2e-10,
                                    "@num_samples": 2e1,
                                    "@channels": 2,
                                    "@unit": "V",
                                    "@vertical_scale": "Volt",
                                },
                            },
                        },
                    },
                    "cal-data": {},
                }
            )
    except FileExistsError:
        print(f"File: {filename} already exists. Please delete it first")


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
    parser.add_argument("-v", "--csv_file", type=str, help="Input CSV file path")
    parser.add_argument(
        "-p", "--pitaya", action="store_true", help="Update with RedPitaya "
    )
    parser.add_argument(
        "-o", "--tektronix", action="store_true", help="Update with Tektronix CSV"
    )
    parser.add_argument(
        "-s", "--schwarz", action="store_true", help="Update with Rohde-Schwarz CSV"
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
    filename = H5FILE_PATH
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
    elif args.tektronix:
        import_hdf5_tektronix(args)
    elif args.schwarz:
        # update_hdf5(args.file_pathtime, ch1_signal)
        # import_hdf5_schwarz(filename, args)
        import_hdf5_rohde(args)

"""
/
├── header/
│   ├── title: "Esther ST Experiment Data"
│   ├── institution": "IPFN-HPL Lab"
│   ├── creation_date: 
│   ├── version: "1.0"
│   └── author:
│
├── experiment/
│   ├── date:
│   ├── name: H2
│   ├── cc_fill_pressure: 40
│   └── gas_ratios:

├── sensors/
│   ├── control-room/
│   └── experimental-hall/
│       ├── cc/
│       │   └── kistler/
│       │       ├── model: ""
│       │       ├── amplifier: "Kistler Type 5015"
│       │       ├── pressure_range: 200 # bar
│       │       ├── wire_number: 504 
│       │       ├── data_key_0: "raw-data/control-room/rohde-schwarz"
│       │       └── data_key_1: "raw-data/control-room/red-pitaya"
│       ├── ct/
│       │   └── kistler/
│       │       ├── model: ""
│       │       ├── amplifier: "Kistler Type 5015"
│       │       ├── pressure_range: "200 # bar
│       │       ├── wire_number: 504 
│       │       └── data_key_0: "raw-data/experimental-hall/rohde-schwarz"
│       ├── st/
│       │   ├── trigger-ports/
│       │   │   ├── model: ""
│       │   │   ├── amplifier: "Thorlabs PDA36A2"
│       │   │   ├── st4: ""
│       │   │   ├── st71/
│       │   │   │    ├── model: ""
│       │   │   │    └── data/
│       │   │   │        ├── key_0: "raw-data/experimental-hall/rohde-schwarz"
│       │   │   │        ├── channel_0: 2 
│       │   │   │        └── key_1: "raw-data/experimental-hall/rohde-schwarz"
│       │   │   ├── st4/
│       │   └── streak-camera/
│       └── dt/
│           └── exit-duct/
│               ├── thyracont/
│               │   ├── model: "VSC43MA4"
│               │   └── pressure_range: "1-1400 mBar" #  (abs)
│               └── honeywell/
│                   ├── model: "VSC43MA4"
│                   ├── pressure_range: "38-3400 mBar" #  (abs)
│                   └── data/
│                       ├── key: "raw-data/experimental-hall/rohde-schwarz"
│                       └── channel: 4
│
├── raw-data/
│   ├── control-room/
│   │   ├── rohde-schwarz/
│   │   │   ├── waveforms/
│   │   │   │   ├── TIME    (unit: s)
│   │   │   │   └── CH1     (unit: V)
│   │   │   └── metadata/
│   │   │       ├── model: "rtb2004"
│   │   │       ├── serial_number: "1333.1005k04/107554"
│   │   │       ├── firmware_version: "02.400"
│   │   │       ├── has_time: True
│   │   │       ├── sample_interval: 2e-10
│   │   │       ├── num_samples: 2e-10
│   │   │       ├── channels: 1
│   │   │       └── vertical_scale: "1,0.05"
│   │   └── red-pitaya/
│   │       ├── waveforms/
│   │       │   └── CH1     (unit: lsb)
│   │       └── metadata/
│   │           ├── model: "STEMlab 125-14"
│   │           ├── has_time: False
│   │           ├── sampling_rate: 125.0e6  # Hz
│   │           ├── decimation: 16
│   │           ├── time_offset: 0.0
│   │           ├── channels: 1
│   │           └── voltage_range: 1.0
│   └── experimental-hall/
│       ├── rohde-schwarz/
│       │   ├── waveforms/
│       │   │   ├── TIME    (unit: s)
│       │   │   ├── CH1     (unit: V)
│       │   │   ├── CH1     (unit: V)
│       │   │   ├── CH1     (unit: V)
│       │   │   └── CH2     (unit: V)
│       │   └── metadata/
│       │       ├── model: "rtb2004"
│       │       ├── serial_number: "1333.1005k04/207766"
│       │       ├── firmware_version: "02.400"
│       │       ├── has_time: True
│       │       ├── sample_interval: 2e-10
│       │       ├── num_samples: 2e-10
│       │       ├── channels: 1
│       │       └── vertical_scale: "1,0.05"
│       ├── tektronix/
│       │   ├── waveforms/
│       │   │   ├── TIME    (unit: s)
│       │   │   ├── CH1     (unit: V)
│       │   │   └── CH1     (unit: V)
│       │   └── metadata/
│       │       ├── model: "mdo4104b-3"
│       │       ├── sample interval: 2e-10
│       │       ├── vertical scale: "1,0.05"
│       └── ...
│   ├── sample interval: 2e-10
│   ├── vertical scale: "1,0.05"
│   │   │    └── attrs: source_file, num_samples, channels, format
│   ├── model: "mdo4104b-3"
│   ├── sample interval: 2e-10
│   ├── vertical scale: "1,0.05"
│   └── ...
"""
