# esther-ops
Esther Shock Tube Operation Manuals

## EPICS Control system 

[Esther Epics repository](https://github.com/ipfn-hpl/esther-epics)

### CSS Archive

1. Check / Start CSS Archive Engine:

CS-Studio [App](https://cs-studio.sourceforge.net/docbook/ch11.html)  for storing data, running as Linux Systemd Service:

```bash
systemctl status epics-css-archive.service
sudo systemctl start epics-css-archive.service
``` 
2. Check if service is running using this [link](http://localhost:4812/main)

### CS-Studio [Phoebus](https://controlssoftware.sns.ornl.gov/css_phoebus/)
1. Start GUI APP: 
```bash
/opt/epics/phoebus.sh
# Else, if you change preference setting file, run:
/opt/epics/phoebus.sh -settings ~/.phoebus/settings.ini
``` 
2. Open *VacuumDisplay* OPI
3. Open *EstherVacuum* OPI


# Esther Subsystems

## Esther Vacuum System

## Combustion Chamber

### Data Acquisition

#### Red Pitaya
nux 
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
streaming-server.local.sh streaming_config_local_ch1_16b_16d_16MS
# if needed:
# mount -o size=128m -t tmpfs tmpfs /tmp/stream_files
``` 
6. Check Server sertting on client PC and run acquisition:
    * Download Client tools [here](https://downloads.redpitaya.com/downloads/Clients/streaming).
 ```bash
rpsa_client --config --hosts=10.zzz.yyy.x --get=VV
rpsa_client --remote --hosts=10.zzz.yyy.x --mode start --verbose
``` 
7. Transfer binary files, logs, etc. and convert to .csv format:
```bash
scp root@rp-f01735:/tmp/stream_files/data_file_2024-xx-xxx.bin\* data_files/
convert_tool data_files/data_file_2024-xxxxx.bin
``` 





