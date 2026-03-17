esther-ops Pulse Sequence
===========

Esther Shock Tube Pulse Operation script

Python Script
------------

1. Check Script Options:
```bash
cd ~/git-repos/esther-ops/pulse-sequence
python3 pulse-ops.py -h
#usage: pulse-ops.py [-h] [-r HOST_RP] [-a] [-s] [-c] [-f] [-t] [-k] [-g KISTLERRANGE] [-m]

#Script to start ESTHER Operation Pulse

#options:
#  -h, --help            show this help message and exit
#  -r HOST_RP, --host_rp HOST_RP
#                        Red Pitay IP address
#  -a, --laserArm        Arm Quantel Laser
#  -s, --laserStandby    Set Quantel in Standby
#  -c, --redpitayaConfig
#                        Check Red Pitaya Config
#  -f, --fire            Fire ESTHER Pulse and acquisition
#  -t, --trigger         Trigger Quantel Laser Q-Switch
#  -k, --kistlerReset    Reset Kistler
#  -g KISTLERRANGE, --kistlerRange KISTLERRANGE
#                        Set Kistler Range
#  -m, --mfcEpics        Start Test Gases MFCs

```
2. E.g. `ARM Ignition Laser`
```bash
python3 pulse-ops.py -a
```
