"""
python3 init_hdf.py -e "H-2" -d "2026-04-09_13-29-09" -k 250.0 -t 11.0 -f 24.83 -r 8.2 2 1.22
python3 init_hdf.py -x
"""

import argparse
import sys

from EstherHDF5Handler import EstherHDF5Handler
from datetime import datetime

H5FILE_PATH = "data_with_metadata.h5"


def init_hdf(args, filename: str = H5FILE_PATH):
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
                        "@he_h2_o2_ratios": args.ratios,
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
                                    "@pressure_range": args.kistler_cc_range,  # Bar
                                    "@data_key_0": "raw-data/control-room/rohde-schwarz/waveforms/C1",
                                    "@data_key_1": "raw-data/control-room/red-pitaya/waveforms/CH1",
                                },
                            },
                            "ct": {
                                "@description": "Compression Tube Section",
                                "kistler": {
                                    "@description": "CC Pressure Kistler Sensor",
                                    "@amplifier": "Kistler Type 5015",
                                    "@wire_number": "501",
                                    "@pressure_range": args.kistler_ct_range,  # Bar
                                    # "@pressure_range": 10,  # Bar
                                    "@data_key_0": "raw-data/experimental-hall/rohde-schwarz/waveforms/C1",
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
                        },
                        "experimental-hall": {
                            "@description": "Instruments in HPL experimental hall",
                        },
                    },
                    "cal-data": {},
                }
            )
            print("HDF5 File Content:")
            for item in h5.list_contents():
                print(f"  {item}")

            all_attributes = h5.list_all_attrs()

            for path, attrs in all_attributes.items():
                print(f"\n{path}:")
                for key, value in attrs.items():
                    print(f"  {key}: {value}")
    except FileExistsError:
        print(f"File: {filename} already exists. Please delete it first")


def explore_hdf(filename: str = H5FILE_PATH):
    with EstherHDF5Handler(filename, mode="r") as h5:
        print("HDF5 File Content:")
        for item in h5.list_contents():
            print(f"  {item}")

        all_attributes = h5.list_all_attrs()

        for path, attrs in all_attributes.items():
            print(f"\n{path}:")
            for key, value in attrs.items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to init Esther Shot HDF5 file")
    parser.add_argument(
        "-x", "--explore", action="store_true", help="Explore with Bunker oscilloscope"
    )
    parser.add_argument(
        "-e", "--experiment_name", type=str, help="Experiment Name", default="S-117"
    )
    parser.add_argument(
        "-d", "--shot_date", type=str, help="Shot date", default="2024-12-26_18-01-03"
    )
    parser.add_argument(
        "-k",
        "--kistler_cc_range",
        type=float,
        help="Kistler CC Range (Bar)",
        default="200.0",
    )
    parser.add_argument(
        "-t",
        "--kistler_ct_range",
        type=float,
        help="Kistler CT Range (Bar)",
        default="10.0",
    )
    parser.add_argument(
        "-f",
        "--fill_pressure",
        type=float,
        help="CC Fill Pressure (Bar)",
        default="40.0",
    )
    # Source - https://stackoverflow.com/a/16016463

    parser.add_argument(
        "-r",
        "--ratios",
        nargs=3,
        metavar=("he", "h2", "o2"),
        help="CC gas mix ratios  (He/H2/O2)",
        type=float,
        default=[8.0, 2.0, 1.2],
    )

    args = parser.parse_args()
    if args.explore:
        with EstherHDF5Handler(H5FILE_PATH, mode="r") as h5:
            print("HDF5 File Content:")
            for item in h5.list_contents():
                print(f"  {item}")

            all_attributes = h5.list_all_attrs()

            for path, attrs in all_attributes.items():
                print(f"\n{path}:")
                for key, value in attrs.items():
                    print(f"  {key}: {value}")
        sys.exit(1)
    init_hdf(args)
    print(args.ratios)
    # explore_hdf()
