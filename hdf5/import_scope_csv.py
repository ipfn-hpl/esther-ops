"""
Here's a Python class for import oscilloscope data in Esther HDF5 Files

https://github.com/ipfn-hpl/esther-ops/tree/main/hdf5

python3 import_scope_csv.py -r ~/Documents/Data-files/RS_ControlRoom/H_2/WFM01.CSV
python3 import_scope_csv.py -b -r ~/Documents/Data-files/RS_Bunker/H_2/WFM04.CSV
"""

import argparse
import sys
import h5py
import numpy as np
import pandas as pd
from pathlib import Path
from parse_csv import parse_tektronix_csv
from EstherHDF5Handler import EstherHDF5Handler

H5FILE_PATH = "data_with_metadata.h5"


def import_pitaya2hdf(args):
    if args.bunker:
        print("Bunker pitaya import not implemented yet.")
        return
    room = "raw-data/control-room/"
    dict_osc = {
        "red-pitaya": {
            "metadata": {
                "@model": "STEMlab 125-14",
                "@hostname": "rp-f01735.local",
                "@ecosystem": "1.04-93661995d",
                "@has_time": False,
                "@sample_rate": 125.0e6,  # Hz
                "@time_offset": 0.0,  # To rohde-schwarz oscilloscope
                "@decimation": 16,
                "@channels": 1,
                "@unit": "lsb",
                "@vertical_range": "+-1V",
            },
        },
    }
    # group: str = "raw-data/red-pitaya/"
    with EstherHDF5Handler(H5FILE_PATH, mode="a") as h5:
        h5.import_from_dict(dict_osc, group_path=room)
    group = room + "red-pitaya/"
    csv_path = Path(args.csv_file)
    # Read CSV - pandas handles scientific notation automatically
    df = pd.read_csv(csv_path, header=None, low_memory=False)
    # Converter para numérico (float) com NaN para '-'
    # df[1] = pd.to_numeric(df[1], errors='coerce')
    # Substituir '-' por 0 ou outro valor
    df[1] = df[1].replace("-", 0)

    with h5py.File(H5FILE_PATH, "a") as hf:
        data = df[1].values.astype(np.int16)
        # ds =
        try:
            data_grp = hf.create_group(group + "waveforms")
            data_grp.create_dataset(
                "CH1", data=data, compression="gzip", compression_opts=4
            )
        except ValueError:
            print(" Unable to create group (name already exists)")


def import_rohde2hdf(
    args,
):  # , group: str = "raw-data/experimental-hall/rohde-schwarz/"):
    csv_path = Path(args.csv_file)
    room = "raw-data/"
    if args.bunker:
        # room = "raw-data/experimental-hall"
        room += "experimental-hall/"
        dict_osc = {
            "rohde-schwarz": {
                "metadata": {
                    "@model": "rtb2004",
                    "@serial_number": "1333.1005k04/107554",
                    "@firmware_version": "02.400",
                    "@has_time": True,
                    "@trigger_source": "C1",
                    "@trigger_type": "edge",
                    "@trigger_slope": "falling",
                    "@unit": "V",
                    "@vertical_scale": "Volt",
                },
            },
        }
    else:
        # print("Rohde-Schwarz import not implemented yet.")
        # room = "raw-data/control-room"
        room += "control-room/"
        dict_osc = {
            "rohde-schwarz": {
                "metadata": {
                    "@model": "rtb2004",
                    "@serial_number": "1333.1005k04/207766",
                    "@firmware_version": "02.400",
                    "@has_time": True,
                    "@trigger_source": "C1",
                    "@trigger_type": "edge",
                    "@trigger_slope": "rising",
                    #                                    "@channels": 4,
                    "@unit": "V",
                    "@vertical_scale": "Volt",
                },
            },
        }
    with EstherHDF5Handler(H5FILE_PATH, mode="a") as h5:
        h5.import_from_dict(dict_osc, group_path=room)
    group = room + "rohde-schwarz/"
    column_info = []
    # Read CSV - pandas handles scientific notation automatically
    df = pd.read_csv(csv_path)
    # Parse column names to extract units (e.g., "C1 in V" -> name="C1", unit="V")
    for col in df.columns:
        if col == "in s":
            # Custom, this is TIME column
            name = "TIME"
            unit = "s"
            print(f"Col O: {col}, N: {name}, U: {unit}")
            column_info.append({"original": col, "name": "TIME", "unit": "s"})
        elif " in " in col:
            name, unit = col.rsplit(" in ", 1)
            print(f"Col O: {col}, N: {name}, U: {unit}")
            column_info.append({"original": col, "name": name, "unit": unit})
        else:
            column_info.append({"original": col, "name": col, "unit": ""})
    # print(f"R Column I: {column_info}")
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
            # if name == "in s":
            #    name = "TIME"
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


def import_tektronix2hdf(args):
    # , group: str = "raw-data/experimental-hall/tektronix/"):
    room = "raw-data/"
    # if args.bunker:
    # room = "raw-data/experimental-hall"
    room += "experimental-hall/"
    dict_osc = {
        "tektronix": {
            "metadata": {
                "@model": "MDO4104B-3",
                "@serial_number": "C020372",
                "@firmware_version": "3.18",
                "@has_time": True,
                "@trigger_source": "CH1",
                "@trigger_type": "edge",
                "@trigger_slope": "rising",
                # "@sample_interval": 2e-10,
                # "@num_samples": 2e1,
                # "@channels": 2,
                "@unit": "V",
                "@vertical_scale": "Volt",
            },
        },
    }
    with EstherHDF5Handler(H5FILE_PATH, mode="a") as h5:
        h5.import_from_dict(dict_osc, group_path=room)
    group = room + "tektronix/"
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


def main():
    parser = argparse.ArgumentParser(
        description="Script to save binary Shot data in HDF5 files"
    )
    parser.add_argument("csv_file", help="Input CSV file path")
    parser.add_argument(
        "-b", "--bunker", action="store_true", help="Update with Bunker oscilloscope"
    )
    parser.add_argument(
        "-t", "--tektronix", action="store_true", help="Update with Tektronix CSV"
    )
    parser.add_argument(
        "-r", "--rohde", action="store_true", help="Update with Rohde-Schwarz CSV"
    )
    parser.add_argument(
        "-p", "--pitaya", action="store_true", help="Update with red-pitaya"
    )
    args = parser.parse_args()
    if not Path(args.csv_file).exists():
        print(f"Error: File '{args.csv_file}' not found.", file=sys.stderr)
        sys.exit(1)
    # parser.add_argument("-c", "--csv", action="store_true", help="Open CSV")
    #
    if args.tektronix:
        import_tektronix2hdf(args)
        sys.exit(1)
    elif args.pitaya:
        import_pitaya2hdf(args)  # , group="raw-data/control-room/rohde-schwarz/")
    elif args.rohde:
        # update_hdf5(args.file_pathtime, ch1_signal)
        # print("Rohde-Schwarz import not implemented yet.")
        import_rohde2hdf(args)  # , group="raw-data/control-room/rohde-schwarz/")
        sys.exit(1)


if __name__ == "__main__":
    main()
