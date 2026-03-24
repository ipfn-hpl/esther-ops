# import h5py
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys

from pathlib import Path

# from read_hdf5 import explore_hdf5, hdf5_file, hdf5_dataset
from EstherHDF5Handler import EstherHDF5Handler


def explore_hdf5(eHdf5):
    print("Contents:")
    for item in eHdf5.list_contents():
        print(f" {item}")

    all_attributes = eHdf5.list_all_attrs()
    for path, attrs in all_attributes.items():
        print(f"\n{path}:")
        for key, value in attrs.items():
            print(f"  {key}: {value}")


def plot_kistler(estherHdf5):
    fig = plt.figure()
    gs = fig.add_gridspec(2, hspace=0.1)
    axs = gs.subplots(sharex=True)
    name = estherHdf5.get_attr("name", "experiment")
    date = estherHdf5.get_attr("date", "experiment")
    fig.suptitle(f"CC Kistler Data Shot: {name} Date: {date}")
    try:
        data = estherHdf5.get_rohde_schwarz_data()
        index = np.argmax(data[1])
        timeMaxRS = data[0][index]
        print(f" schwarz max index {index}, time: {timeMaxRS}")
        axs[0].set_title("Rohde-Schwarz Oscilloscope", fontsize="small", loc="right")
        axs[0].plot(
            data[0],
            data[1],
            color="blue",
        )  # alpha=0.5)
        axs[0].set_ylabel("Pressure / Bar")
        axs[0].grid()
    except KeyError:
        print("object 'raw-data/cc/kistler/rohde-schwarz' doesn't exist in dataset")
    try:
        data = estherHdf5.get_red_pitaya_data()
        index = np.argmax(data[1])
        timeMaxRP = data[0][index]
        print(f"pitaya max index {index}, time: {timeMaxRP}")
        timeOffSet = timeMaxRS - timeMaxRP
        print(f"pitaya TimeOffset  {timeOffSet} ms ")
        print
        axs[1].plot(
            data[0],
            data[1],
            color="red",
        )  # alpha=0.5)
        axs[1].set_title("Red Pitaya ADC Ch1", fontsize="small", loc="right")
        axs[1].grid()
    except KeyError:
        print("object 'red-pitaya' doesn't exist in dataset")
    fig.supxlabel("Time / ms")
    plt.show()


# Example usage
if __name__ == "__main__":
    # Replace with your HDF5 file path
    # filename = "data_with_metadata.h5"
    parser = argparse.ArgumentParser(
        description="Script to plot dataset Shot data stored in HDF5 files"
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
        default="/raw-data/rohde-schwarz-cc",
    )
    parser.add_argument("-e", "--explore", action="store_true", help="Explore hdf5")
    parser.add_argument("-p", "--pitaya", action="store_true", help="Plot RedPitaya ")
    parser.add_argument("-a", "--afs", action="store_true", help="Read from AFS")
    parser.add_argument(
        "-s", "--schwarz", action="store_true", help="Plot with rohde-Schwarz CSV"
    )
    parser.add_argument(
        "-m",
        "--maxrows",
        type=int,
        help="The maximum number of rows to plot.",
        default="1000000",
    )
    parser.add_argument(
        "-r",
        "--reportId",
        type=int,
        help="The report id number.",
        default=316,
    )
    parser.add_argument(
        "-o",
        "--offset",
        type=float,
        help="The time offset of the RedPitaya data.",
        default=1.0e27,
    )
    # parser.add_argument(
    #    "-d", "--decim", type=int, help="Plot decimation", default="100"
    # )
    args = parser.parse_args()

    # First, explore the structure
    try:
        if args.afs:
            path = Path("/afs/ist.utl.pt/groups/esther/HDF5")
            new_path = path.joinpath(str(args.reportId))
            # print(f"new_path {new_path}")
            file_path = new_path.joinpath("data_with_metadata.h5")
        else:
            file_path = args.file_path

        if args.offset != 1.0e27:
            # 'r+': Read/write access without deleting existing data.
            with EstherHDF5Handler(file_path, mode="r+") as h5:
                h5.change_offset_red_pitaya(args.offset)
                h5.close()
            # sys.exit()
        else:
            with EstherHDF5Handler(file_path, mode="r") as h5:
                if args.explore:
                    explore_hdf5(h5)
                else:
                    plot_kistler(h5)
                # explore_hdf5(args.file_path)
    except FileNotFoundError:
        print(
            f"File '{args.file_path}' not found. Please provide a valid HDF5 file path."
        )
