#!/home/esther/.local/venvs/python-epics/bin/python3

#
#!/usr/bin/env python3
"""
This script uses a pip package
https://github.com/Terrabits/rohdeschwarz

Example commands are in:
https://github.com/Rohde-Schwarz/Examples/blob/main/Oscilloscopes/Python/RsInstrument/RsInstrument_gi2000_Example.py

https://www.rohde-schwarz.com/us/driver-pages/remote-control/remote-programming-environments_231250.html
"""

# from rohdeschwarz import print_header
from rohdeschwarz.instruments import GenericInstrument

gi = GenericInstrument() 
# Open TCP socket connection (no VISA)
# with defaults:
# address '127.0.0.1', port 5025
gi.open_tcp('192.168.0.32')

# Create SCPI command log
gi.open_log('SCPI_Command_Log.txt')

# Print headers:
# print_header(gi.log, "gi Example", "0.0.1")
gi.print_info()

# Send SCPI commands manually:
gi.write('*IDN?')
gi.read()
gi.query('*IDN?')

# Get id string:
gi.id_string()

# Test if Rohde & Schwarz instrument:
gi.is_rohde_schwarz()

# gi basics

# Preset the instrument:
gi.preset()

# -----------------------------------------------------------
# Basic Settings:
# ---------------------------- -------------------------------
# gi.write("TIM:ACQT 1.2")  # 10ms Acquisition time
gi.write("TIM:SCAL 0.1")  # 10ms Acquisition time
gi.write("CHAN1:RANG 10.0")  # Horizontal range 5V (0.5V/div)
gi.write("CHAN1:OFFS 3.0")  # Offset 0
gi.write("CHAN1:COUP DC")  # Coupling AC 1MOhm
gi.write("CHAN1:STAT ON")  # Switch Channel 1 ON

# -----------------------------------------------------------
# Trigger Settings:
# -----------------------------------------------------------
gi.write("TRIG:A:MODE AUTO")  # Trigger Auto mode in case of no signal is applied
gi.write(
        "TRIG:A:TYPE EDGE;"
        ":TRIG:A:EDGE:SLOP POS")  # Trigger type Edge Positive
gi.write("TRIG:A:SOUR CH1")  # Trigger source CH1
gi.write("TRIG:A:LEV1 1.5")  # Trigger level 0.05V
# gi.query_opc()  # Using *OPC? query waits until all the instrument settings are finished

# Pause until previous command
# completes:
gi.pause(timeout_ms=4000)
# gi.write('RUN')
gi.write('STOP')

# Query error
# returns bool
gi.is_error()

# Get errors
# list of tuples of format:
# [(error_code, 'Error string'),...]
gi.errors

# Clear status/errors
gi.clear_status()

gi.write("HCOP:LANG PNG;:MMEM:NAME 'Dev_Screenshot'")  # Hardcopy settings for taking a screenshot - notice no file extension here
gi.write("HCOP:IMM")  # Make the screenshot now
gi.pause()
#gi.query_opc()  # Wait for the screenshot to be saved

#gi.read_block_data_to_file('filename.png')

# Close the session
gi.close()
