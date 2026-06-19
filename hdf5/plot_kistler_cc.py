import argparse

import numpy as np
import matplotlib.pyplot as plt
import h5py
import sys

import logging
import psycopg2
from pathlib import Path

from db_config import DB_CONFIG

log = logging.getLogger("plot_kistler")


def get_attr(hdf, path: str = "/", key: str = "") -> any:
    """get a single attribute value."""
    obj = hdf if path == "/" else hdf[path]
    return obj.attrs[key]


def plot_kistler(hdf, reportId: int = 316):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM get_cc_shot_params((%s))"
                cur.execute(
                    query,
                    (reportId,),
                )
                result = cur.fetchone()
                print(f"result {result}")
                ambientPressure = result[0]
                ccFillPressure = result[1]
                ccRangeKistler = result[2]
                ccDeltaPKistler = result[3]
                print(f"ambientPressure: {ambientPressure}")
                """
                query = "SELECT float_val from sample WHERE short_name='ambientPressure' AND reports_id=(%s)"

                cur.execute(
                    query,
                    (reportId,),
                )
                ambientPressure = cur.fetchone()[0]
                print(f"ambientPressure: {ambientPressure}")
                query = (
                    "SELECT float_val from sample WHERE short_name='PT901' "
                    "AND pulse_phase='CC_Step8_End' AND reports_id=(%s)"
                )
                cur.execute(
                    query,
                    (reportId,),
                )
                ccFillPressure = cur.fetchone()[0]
                query = (
                    "SELECT float_val from sample WHERE short_name='CC_Range_Kistler' "
                    "AND pulse_phase='CC_Pulse' AND reports_id=(%s)"
                )
                cur.execute(
                    query,
                    (reportId,),
                )
                ccRangeKistler = cur.fetchone()[0]
                print(f"ccRangeKistler: {ccRangeKistler}")
                query = (
                    "SELECT float_val from sample WHERE short_name='CC_DeltaP_Kistler' "
                    "AND pulse_phase='CC_Pulse' AND reports_id=(%s)"
                )
                cur.execute(
                    query,
                    (reportId,),
                )
                ccDeltaPKistler = cur.fetchone()[0]
                """
                print(f"ccDeltaPKistler: {ccDeltaPKistler}")

    except psycopg2.Error as exc:
        log.error("Database error: %s", exc)
    fig = plt.figure()
    gs = fig.add_gridspec(2, hspace=0.1)
    axs = gs.subplots(sharex=True)
    key = ""
    try:
        exp = hdf["experiment"]
        attrs = dict(exp.attrs)  # h5.get_attrs("diagnostics/experimental-hall/cc")
        # key = "cc_fill_pressure"
        # fill_pressure = attrs[key]
        date = attrs["date"]

        # print(f"fill_pressure: {fill_pressure} Bar, date {date}")
        diag = hdf["diagnostics/experimental-hall/cc/kistler"]
        attrs = dict(diag.attrs)  # h5.get_attrs("diagnostics/experimental-hall/cc")
        # key = "pressure_range"
        # kistler_range = attrs[key]
        kistler_scale = ccRangeKistler / 10.0  # Bar per Volt
        print(f"Attributes: {attrs}")
        key = "raw-data/control-room/rohde-schwarz/waveforms/TIME"
        rtime = hdf[key][:]
        key = "raw-data/control-room/rohde-schwarz/waveforms/C1"
        rdata = hdf[key][:]
        print(rdata.shape)
        # r_data = estherHdf5.get_rohde_schwarz_data()
        index = np.argmax(rdata)
        timeMaxRS = rtime[index]
        print(f" schwarz max index {index}, time: {timeMaxRS}")
        axs[0].set_title("Rohde-Schwarz Oscilloscope", fontsize="small", loc="right")
        axs[0].plot(
            rtime,
            rdata * kistler_scale + ccFillPressure,
            color="blue",
        )  # alpha=0.5)
        axs[0].set_ylabel("Pressure / Bar")
        axs[0].grid()
        #

        rObj = "raw-data/control-room/red-pitaya/metadata"
        red = hdf[rObj]
        attrs = dict(red.attrs)  # h5.get_attrs("diagnostics/experimental-hall/cc")
        print(f"Red Attributes: {attrs}")
        key = "sample_rate"
        sample_rate = get_attr(hdf, rObj, key)
        key = "decimation"
        decimation = get_attr(hdf, "raw-data/control-room/red-pitaya/metadata", key)
        key = "time_offset"
        time_offset = get_attr(hdf, rObj, key)

        key = "raw-data/control-room/red-pitaya/waveforms/CH1"
        pdata = hdf[key][:]

        print(f"Data shape: {pdata.shape}, sample_rate: {sample_rate} Hz")
        time = np.arange(pdata.shape[0]) / sample_rate * decimation + time_offset
        index = np.argmax(pdata)
        timeMaxRP = time[index]
        print(f"pitaya max index {index}, time: {timeMaxRP}")
        timeOffSet = timeMaxRS - timeMaxRP
        print(f"Measured RedPitaya TimeOffset  {timeOffSet} ms ")
        axs[1].plot(
            time,
            pdata,
            color="red",
        )  # alpha=0.5)
        axs[1].set_title("Red Pitaya ADC Ch1", fontsize="small", loc="right")
        axs[1].grid()
    except KeyError:
        print(f"object '{key}' doesn't exist in dataset")
    fig.supxlabel("Time / ms")
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Script to plot dataset Shot data stored in HDF5 files"
    )
    parser.add_argument(
        "-t", "--tree", action="store_true", help="Read hdf5 from SSHFS tree"
    )
    parser.add_argument("-r", "--reportId", type=int, default=316, help="reportID ")

    parser.add_argument(
        "-f",
        "--file_h5",
        type=str,
        help="File to read",
        default="data_with_metadata.h5",
    )
    parser.add_argument(
        "-o",
        "--offset",
        type=float,
        help="The time offset of the RedPitaya data.",
        default=1.0e27,
    )
    args = parser.parse_args()

    if args.tree:
        p = Path("./hdf-files")
        path_h5 = p / str(args.reportId) / "data_with_metadata.h5"
    else:
        path_h5 = Path(args.file_h5)
    if not path_h5.exists():
        print(f"Error: File '{args.file_h5}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.offset != 1.0e27:
        # 'r+': Read/write access without deleting existing data.
        with h5py.File(path_h5, "r+") as h5:
            rkey = "raw-data/control-room/red-pitaya/metadata"
            dataset = h5[rkey]
            dataset.attrs["time_offset"] = args.offset
            sys.exit(1)
    with h5py.File(path_h5, "r") as h5:
        # temp_data = h5["raw-data/control-room/rohde-schwarz/waveforms/C1"][:]
        print(f"Type of h5: {type(h5)}")
        plot_kistler(h5, args.reportId)


if __name__ == "__main__":
    main()
