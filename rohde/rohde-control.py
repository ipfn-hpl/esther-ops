#!/home/esther/.local/venvs/python-epics/bin/python3

#!/usr/bin/env python3
"""

This script uses a pip package
https://github.com/Terrabits/rohdeschwarz

"""

import argparse
from rohdeschwarz.instruments import GenericInstrument


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
        print(self.gi.id_string())
        print(self.gi.print_info())

    def test(self):
        if self.gi.is_rohde_schwarz():
            print("It is R&S")

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

    parser.add_argument('-r', '--host_rp', default='192.168.0.35',
                        help='Rohde & Schwarz IP address')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    rS = rohdeCom()
    rS.test()
    # rS.basic_settings(1)
    rS.channel_config(1, 5.0)
    rS.trigger_config(2, 2.0)
    #rS.stop()
    rS.run()
    rS.close()

