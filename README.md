# esther-ops
Esther Shock Tube Operation Manuals

## EPICS Control system 

[Esther Epics repository](https://github.com/ipfn-hpl/esther-epics)

### CSS Archive

1. Check / Start CSS Archive Engine:

CS-Studio [App](https://cs-studio.sourceforge.net/docbook/ch11.html)  for storing data, running as Linux Systemd Service:

```bash
systemctl status epics-css-archive.servicei
# If necessary
sudo systemctl start epics-css-archive.service
``` 
2. Check if service is running using this [link](http://localhost:4812/main)

### CS-Studio [Phoebus](https://controlssoftware.sns.ornl.gov/css_phoebus/)
1. Start GUI APP: 
```bash
/opt/epics/phoebus.sh
# Else, if you changed preference settings file, run:
/opt/epics/phoebus.sh -settings ~/.phoebus/settings.ini
``` 
2. Open *VacuumDisplay* OPI
3. Open *EstherVacuum* OPI


# Esther Subsystems

## Esther Vacuum System

## Combustion Chamber GAS SYSTEM Control

### Start Systems:

1. Login to golem PC with esther account
2. Check if Gas Switchboard is powered
  * Wait 3 min and check if all Epics IOCs are running
```bash
ssh rpi2-gas
>sudo systemctl status esther-gas-ioc.service
>exit

ssh rpi4-gas
>sudo systemctl status esther-mfc-ioc.service
>exit

ssh galatea
>sudo systemctl status esther-vacuum-ioc.service
>sudo systemctl status epics-python-caput.service
>exit

ssh rpi4-vacuum
>sudo systemctl status esther-vacuum-ioc.service
>exit
```


## Data Acquisition

#### Red Pitaya

1. *Hardware* [Red Pitaya](https://redpitaya.com/stemlab-125-14/) Board
2. *Software*
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
# if needed:
mount -o size=128m -t tmpfs tmpfs /tmp/stream_files
streaming-server.local.sh streaming_config_local_ch1_16b_16d_16MS
``` 
6. Check Server sertting on client PC and run manual acquisition:
    * Download Client tools [here](https://downloads.redpitaya.com/downloads/Clients/streaming).
 ```bash
rpsa_client --detect
rpsa_client --config --hosts=10.zzz.yyy.x --get=VV
rpsa_client --remote --hosts=10.zzz.yyy.x --mode start --verbose
``` 
7. Transfer binary files, logs, etc. and convert to .csv format:
```bash
cd ~/git-repos/esther-ops/red-pitaya
scp root@rp-f01735:/tmp/stream_files/data_file_202y-xx-xxx.bin\* data_files/
convert_tool data_files/data_file_2024-xxxxx.bin
``` 


## Automated Pulse Trigger and  Data Acquisition Sequence.

1. Start Red pitaya server as described in previous step.  Note IP address.
2. Login to golem PC
3. Check Program Options:
 ```bash
 cd ~/git-repos/esther-python/pulse-schedule
./pulse-start.py -h  
``` 
4. Check Red Pitaya Acquisition Config 
```bash
./pulse-start.py -r 10.10.136.2xx -c
``` 
5. Arm Quantel Laser single pulse and Start Flash lamp
```bash
./pulse-start.py -a
``` 
6. Fire Laser and Acquisition
```bash
./pulse-start.py -r 10.10.136.2xx -f
``` 
7. Set Quantel Laser to Standby  Mode
```bash
./pulse-start.py -s
``` 
8. Transfer Red Pitaya files and convert to csv, if necessary.
```bash
cd ~/git-repos/esther-ops/red-pitaya
scp root@rp-f01735.local:/tmp/stream_files/data_file_202y-xx-xxx.bin\* data_files/
convert_tool data_files/data_file_2024-xxxxx.bin
``` 
9. Plot Red Pitaya Plots
 ```bash
./plotRPbin.py -m 10000000 -f data_files/data_file_2024-xxxxx  # (no extension)
``` 


