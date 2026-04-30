#!/usr/bin/env python3
"""
CSV to HDF5 Converter for Tektronix oscilloscope data.

Supports CSV format:
1. Tektronix MDO format: Metadata header followed by TIME,CH1,CH2,... data
2. Rohde-Schwarz CSV for oscilloscope data.
"""

import argparse
import csv
import sys
from pathlib import Path

# import h5py
import numpy as np
import pandas as pd


def parse_rohde_csv(csv_path: Path):  ##  -> tuple[dict, pd.DataFrame]:
    """
    Parse Rohde  CSV with metadata header.

    Returns
    -------
    tuple[dict, pd.DataFrame]
        Metadata dictionary and data DataFrame.
    """
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

        # for info in column_info:
    #   data = df[info["original"]].values.astype(np.float32)
    # ds = hf.create_dataset(
    #    info["name"], data=data, compression="gzip", compression_opts=4
    # )
    # Store unit as attribute
    # if info["unit"]:
    #    ds.attrs["unit"] = info["unit"]

    # Store metadata
    # hf.attrs["source_file"] = csv_path.name
    # hf.attrs["num_samples"] = len(df)
    # hf.attrs["columns"] = [info["name"] for info in column_info]
    return column_info


def parse_tektronix_csv(csv_path: Path) -> tuple[dict, pd.DataFrame]:
    """
    Parse Tektronix MDO-style CSV with metadata header.

    Returns
    -------
    tuple[dict, pd.DataFrame]
        Metadata dictionary and data DataFrame.
    """
    metadata = {}
    header_line = None
    data_start_line = None

    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row or all(cell.strip() == "" for cell in row):
                continue

            first_cell = row[0].strip()

            # Detect data header (TIME,CH1,CH2,...)
            if first_cell.upper() == "TIME":
                header_line = i
                data_start_line = i + 1
                # Store column names
                metadata["_columns"] = [c.strip() for c in row if c.strip()]
                break

            # Parse metadata key-value pairs
            if len(row) >= 2 and first_cell:
                key = first_cell
                values = [v.strip() for v in row[1:] if v.strip()]
                if len(values) == 1:
                    metadata[key] = values[0]
                elif len(values) > 1:
                    metadata[key] = values

    if header_line is None:
        raise ValueError("Could not find data header (TIME,CH1,...) in file")

    # Read data portion
    df = pd.read_csv(
        csv_path, skiprows=data_start_line, names=metadata["_columns"], header=None
    )

    return metadata, df


def main():
    parser = argparse.ArgumentParser(
        description="Convert Tektronix oscilloscope CSV data to Pandas."
    )
    parser.add_argument("csv_file", help="Input CSV file path")
    parser.add_argument("-o", "--output", help="Output HDF5 file path (optional)")

    args = parser.parse_args()

    if not Path(args.csv_file).exists():
        print(f"Error: File '{args.csv_file}' not found.", file=sys.stderr)
        sys.exit(1)

    #    output_path = csv_to_hdf5(args.csv_file, args.output)
    # Tektronix MDO format
    csv_path = Path(args.csv_file)
    column_info = parse_rohde_csv(csv_path)
    print(f"R Column I: {column_info}")
    metadata, df = parse_tektronix_csv(args.csv_file)
    columns = metadata.pop("_columns")
    print(f"T Columns: {columns}")


if __name__ == "__main__":
    main()
