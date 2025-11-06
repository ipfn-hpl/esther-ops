#!/home/esther/.local/venvs/python-epics/bin/python3

#!/usr/bin/env python3
"""

This script uses a pip package
https://github.com/Terrabits/rohdeschwarz

"""

import argparse
from rohdeschwarz.instruments import GenericInstrument

IP_CC = '192.168.0.35'
IP_CT = '192.168.0.36'

class rohdeCom():
    """
    GenericInstrument
    """
    def __init__(self, ip_port='192.168.0.35',
                 log_file='SCPI_Command_Log.txt'):
        self.gi = GenericInstrument()
        self.gi.open_tcp(ip_port)
        self.gi.query('*IDN?')
        self.gi.open_log(log_file)
        # Print headers:
        # print_header(gi.log, "gi Example", "0.0.1")

    def test(self):
        if self.gi.is_rohde_schwarz():
            print("It is R&S")
            print(self.gi.id_string())
            print(self.gi.print_info())

    def stop(self):
        self.gi.write("STOP")

    def run(self):
        self.gi.write("RUN")

    def trigger_mode(self, mode="AUTO"):
        self.gi.write(f"TRIG:A:MODE {mode:s}")  # Trigger

    def trigger_config(self, channel=1, level=1.3):
        if channel < 1:
            return
        if channel > 4:
            return
        # self.gi.write("TRIG:A:MODE AUTO")  # Trigger Auto mode in case of no signal is applied
        self.trigger_mode("NORM")
        self.gi.write(
                "TRIG:A:TYPE EDGE;"
                ":TRIG:A:EDGE:SLOP POS")  # Trigger type Edge Positive
        self.gi.write(f"TRIG:A:SOUR CH{channel:d}")  # Trigger source CH1
        # Selects the trigger input. 1...4 select the corresponding analog
        # redundant?
        self.gi.write(f"TRIG:A:LEV{channel:d}:VAL {level:f}")  # Trigger level 0.05V

    def ct_config(self):
        self.gi.write("*RST")  # reset
        self.gi.write("ACQ:POIN:AUT ON")  # The instrument fits to the selected timebase.
        self.gi.write("TIM:SCAL 0.1")  # 10ms Acquisition time
        self.gi.write("TIMebase:POSition 0.4")
        self.gi.write("CHAN1:RANG 10")  # Horizontal range 10V (1V/div)
        # self.gi.write("CHAN1:OFFS -1.0")
        self.gi.write("CHAN1:POSition -4.0") # vertical position of the waveform in divisions
        self.gi.write("CHAN1:COUP DC")
        self.gi.write("CHAN1:STAT ON")

        self.gi.write("CHAN2:RANG 1.0")  # Horizontal range 10V (1V/div)
        self.gi.write("CHAN2:POSition -3.0")
        self.gi.write("CHAN2:STAT ON")
        self.gi.write("CHAN3:STAT ON")
        self.gi.write("TRIG:A:MODE NORM")
        self.gi.write("TRIG:A:TYPE EDGE")
        self.gi.write("TRIG:A:EDGE:SLOP POS")  # Trigger type Edge Positive
        self.gi.write("TRIG:A:SOUR CH1")
        self.gi.write("TRIG:A:LEV1:VAL 1.0")  # Trigger level
        self.gi.write("RUN")
        # self.gi.write("RUNSingle")

    def cc_config(self):
        self.gi.write("*RST")  # reset
        self.gi.write("ACQ:POIN:AUT ON")  # The instrument fits to the selected timebase.
        self.gi.write("TIM:SCAL 0.1")  # 10ms Acquisition time
        self.gi.write("TIMebase:POSition 0.4")
        self.gi.write("CHAN1:RANG 10")  # Horizontal range 10V (1V/div)
        # self.gi.write("CHAN1:OFFS -1.0")
        self.gi.write("CHAN1:POSition -4.0") # vertical position of the waveform in divisions
        self.gi.write("CHAN1:COUP DC")
        self.gi.write("CHAN1:STAT ON")
        self.gi.write("CHAN2:STAT ON")
        self.gi.write("CHAN3:STAT OFF")
        self.gi.write("TRIG:A:MODE NORM")
        self.gi.write("TRIG:A:TYPE EDGE")
        self.gi.write("TRIG:A:EDGE:SLOP POS")  # Trigger type Edge Positive
        self.gi.write("TRIG:A:SOUR CH1")
        self.gi.write("TRIG:A:LEV1:VAL 1.0")  # Trigger level
        #self.gi.write("RUN")
        self.gi.write("RUNSingle")

    def channel_config(self, channel=1, range=10.0):
        chString = f"CHAN{channel:d}, R:{range:0.2f}"
        if channel < 1:
            return
        if channel > 4:
            return

        print(chString)
        # gi.write("TIM:ACQT 1.2")  # 10ms Acquisition time
        self.gi.write("TIM:SCAL 0.1")  # 10ms Acquisition time
        self.gi.write(f"CHAN{channel:d}:RANG {range:0.2f}")  # Horizontal range 10V (1V/div)
        self.gi.write(f"CHAN{channel:d}:OFFS 3.0")  # Offset 
        self.gi.write(f"CHAN{channel:d}:COUP DC")  # Coupling
        self.gi.write(f"CHAN{channel:d}:STAT ON")  # Switch Channel  ON

    def basic_settings(self, channel):
        chString = f"CHAN{channel:d}"
        if channel < 1:
            return
        if channel > 4:
            return

        print(chString)
        # gi.write("TIM:ACQT 1.2")  # 10ms Acquisition time
        self.gi.write("TIM:SCAL 0.1")  # 10ms Acquisition time
        self.gi.write(f"CHAN{channel:d}:RANG 10.0")  # Horizontal range 10V (1V/div)
        self.gi.write(f"CHAN{channel:d}:OFFS 3.0")  # Offset 0
        self.gi.write(f"CHAN{channel:d}:COUP DC")  # Coupling 
        self.gi.write("CHAN2:STAT ON")  # Switch Channel 1 ON

    def close(self):
        self.gi.clear_status()
        self.gi.close_log()
        self.gi.close()


def parse_args():
    parser = argparse.ArgumentParser(
            description='Script to Control Rohde & Schwarz Oscilloscope')

    parser.add_argument('-s', '--stop',
                        action='store_true', help='Stop Aqc')
    parser.add_argument('-r', '--run',
                        action='store_true', help='Start Aqc')
    parser.add_argument('-c', '--cc_config',
                        action='store_true', help='Config CC Osc')
    parser.add_argument('-t', '--ct_config',
                        action='store_true', help='Config CT Osc')
    parser.add_argument('-p', '--host_rs', default='192.168.0.35',
                        help='Rohde & Schwarz IP address')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.ct_config:
        rS = rohdeCom(ip_port=IP_CT)
        rS.ct_config()
        # rS.test()
        rS.close()
        exit()
    if args.cc_config:
        rS = rohdeCom(ip_port=IP_CC)
        rS.cc_config()
        # rS.test()
        rS.close()
        exit()
    rS = rohdeCom(args.host_rs)
    if args.stop:
        rS.stop()
        exit()
    if args.run:
        rS.run()
        exit()

    rS.test()
    # rS.basic_settings(1)
    rS.channel_config(1, 5.0)
    rS.trigger_config(2, 2.0)
    rS.run()
    rS.close()

