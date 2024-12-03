#!/usr/bin/env python3
"""
This example demonstrates many of the 2D plotting capabilities
in pyqtgraph. All of the plots may be panned/scaled by dragging with 
the left/right mouse buttons. Right click on any plot to show a context menu.
"""

import numpy as np
import os
import argparse
import pyqtgraph as pg
import pyqtgraph.exporters

# from pyqtgraph.Qt import QtCore

# PLOT_DECIM = 100
RP_DECIM = 16

def read_csv_data(args):
    # data = np.genfromtxt(filename, delimiter=" ", dtype='int16')
    data = np.loadtxt(args.file, delimiter=',', max_rows=args.maxrows)
    # data = np.loadtxt(filename)
    # dataC = np.fromfile(filename, dtype='uint32')
    # ‘F’ means to readthe elements using Fortran-like index order,
    # with the first index changing fastest,
    # data_mat = np.reshape(data, (8, - 1), order='F')
    # data_cnt64 = np.reshape(dataC, (4, -1), order='F')
    # x = np.arange(data.shape[1])
    return data


def read_bin_data(filepath):
    # data = np.fromfile(filename, dtype='int16')
    data = np.fromfile(f"{filepath}.bin", dtype='<i2')
    # data = np.memmap(filename, dtype=np.dtype('<i2'), mode='r')
    # dataC = np.fromfile(filename, dtype='uint32')
    # ‘F’ means to readthe elements using Fortran-like index order,
    # with the first index changing fastest,
    # data_mat = np.reshape(data, (8, - 1), order='F')
    # data_cnt64 = np.reshape(dataC, (4, -1), order='F')
    # x = np.arange(data.shape[1])
    # decim_data = data[40::PLOT_DECIM]
    # segSize = 16430  #
    # segOffset = 40
    Head = 40
    Foot = 6
    segSize = 16384 + Head + Foot  # 16430
    signal = np.array([], dtype='int16')
    for i in range(0, len(data), segSize):
        segment = data[i:i+segSize]
        signal = np.append(signal, segment[Head:-Foot])
    return data, signal


parser = argparse.ArgumentParser(
        description='Script to extract temperature from Edwards GX Pumps')
parser.add_argument('-c', '--csv',
                    action='store_true', help='Open CSV')
parser.add_argument('-f', '--file', type=str,
                    help='File to read', default='dataXX.bin')
parser.add_argument('-m', '--maxrows', type=int,
                    help='The maximum number of rows to read.',
                    default='1000000')
parser.add_argument('-d', '--decim', type=int,
                    help='Plot decimation',
                    default='100')
args = parser.parse_args()

app = pg.mkQApp("Plotting Example")
# mw = QtWidgets.QMainWindow()
# mw.resize(800,800)

# Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
win.resize(1000, 600)
win.setWindowTitle('Plotting Red Pitaya Data')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# p1 = win.addPlot(title="Basic array plotting", y=np.random.normal(size=100))
# p2 = win.addPlot(title="Multiple curves")
# p2.plot(np.random.normal(size=100), pen=(255,0,0), name="Red curve")

# win.nextRow()
if args.csv:
    data = read_csv_data(args)
else:
    data, signal = read_bin_data(args.file)

print(f"Data len: {len(signal)}")
dirname, basename = os.path.split(args.file)
p1 = win.addPlot(title=f"RP plot {basename:s}")
data2Plot = signal[:args.maxrows]
# data2Plot = signal[:args.maxrows:args.decim]
x = np.arange(0, len(data2Plot), dtype='int') / 125e6 * RP_DECIM
p1.addLegend()
p1.plot(x, data2Plot, pen=(255, 0, 0), name="RP CH1")
p1.showGrid(x=True, y=True, alpha=0.3)
p1.setLabel('bottom', "Time", units='s')
# updatePlot()
# create an exporter instance, as an argument give it
# the item you wish to export
#exporter = pg.exporters.ImageExporter(plt.plotItem)
exporter = pg.exporters.ImageExporter(win.scene())
# save to file
exporter.export(f'{basename}.png')

if __name__ == '__main__':
    pg.exec()
