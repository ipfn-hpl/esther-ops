# esther-ops
Esther Shock Tube Operation Manuals

## EPICS Control system 

[Esther Epics repository](https://github.com/ipfn-hpl/esther-epics)

### CSS Archive

1. Check / Start CSS Archive Engine

CS--Studio App dor storing data. [cs-studio](https://cs-studio.sourceforge.net/docbook/ch11.html)  running as Systemd service 

```bash
systemctl status epics-css-archive.service
systemctl start epics-css-archive.service
``` 
2. Check if service is running in this [link](http://localhost:4812/main)

# Esther Subsystems

## Esther Vacuum System

## Combustion Chamber

### Data Acquisition

#### Red Pitaya

1. *Hardware* [Red Pitaya](https://redpitaya.com/stemlab-125-14/) Board
2. Software
    * Red Pitaya GNU/Linux Ecosystem
    * Version: 1.04-93661995d [Stable Images](https://downloads.redpitaya.com/downloads/STEMlab-125-1x)
3. Connected to HPL network (10.zzz.yyy.xxx)
    * After power-up should have Blue and Green LEDs steady, red blinking.
4. Connect with:

```bash
ssh root@rp-f01735.local
``` 

5. Start Streaming server, take note of IP address, and start server:
 ```bash
ping rp-f01735.local
ssh root@rp-f01735.local
ip address
mount -o size=128m -t tmpfs tmpfs /tmp/stream_files
streaming-server.local.sh streaming_config_local_ch1_16b_16d_8MS
``` 
6. Check Server sertting on client PC and run acquisition:
    * Download Client tools [here](https://downloads.redpitaya.com/downloads/Clients/streaming).
 ```bash
rpsa_client --config --hosts=10.zzz.yyy.x --get=VV
rpsa_client --remote --hosts=10.zzz.yyy.x --mode start --verbose
``` 
7. Tranfers binary files, logs, etc and convert to .csv format:
```bash
scp root@rp-f01735:/tmp/stream_files/data_file_2024-xx-xxx.bin\* data_files/
convert_tool data_files/data_file_2024-xxxxx.bin
``` 





