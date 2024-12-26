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

1. Open terminal in golem PC, with esther account
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
# on first acquisition, if needed:
streaming-server.local.sh streaming_config_local_ch1_16b_16d_16MS
mount -o size=128m -t tmpfs tmpfs /tmp/stream_files
``` 
6. Check Server serttings on client PC:
    * Download Client tools [here](https://downloads.redpitaya.com/downloads/Clients/streaming).
 ```bash
rpsa_client --detect
rpsa_client --config --hosts=10.zzz.yyy.x --get=VV
``` 

(Skip next steps if are using *Automated Pulse Sequence*, next section)

7. Run manual acquisition:
 ```bash
rpsa_client --remote --hosts=10.zzz.yyy.x --mode start --verbose
``` 
8. Transfer binary files, logs, etc. and convert to .csv format:
```bash
cd ~/git-repos/esther-ops/red-pitaya
scp root@rp-f01735:/tmp/stream_files/data_file_202y-xx-xxx.bin\* data_files/
convert_tool data_files/data_file_2024-xxxxx.bin
``` 


## Automated Pulse Trigger and  Data Acquisition Sequence.

1. Start Red pitaya server as described in previous step.  Note IP address.
2. Open terminal in golem PC, with esther account
3. Check Program Options:
 ```bash
 cd ~/git-repos/esther-ops/pulse-sequence
./pulse-ops.py -h  
``` 
4. Check Red Pitaya Acquisition Config 
```bash
./pulse-ops.py -r 10.10.136.2xx -c
``` 
5. Arm Quantel Laser single pulse and Start Flash lamp
```bash
./pulse-ops.py -a
``` 
6. Fire Laser and Acquisition Sequence
```bash
./pulse-ops.py -r 10.10.136.2xx -f
``` 
7. Set Quantel Laser to Standby Mode (Stop Flash lamp)
```bash
./pulse-ops.py -s
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

## Streak Camera Trigger System
[FPGA Project Repo](https://github.com/bernardocarvalho/ad-ipfn-hdl), branch 'esther_trigger_2019.1'   
[Linux Device  Driver and apps Repo](https://github.com/ipfn-hpl/esther_dma_ip_drivers), branch 'esther_trigger_2019.1'

1. Start PC and load FPGA board drivers
2. Open terminal in ACIS PC, with esther account
 ```bash
ssh esther@acis.local  # or just: `ssh acis`
ll /dev/fmc_xdma0_*
lsmod| grep xdma
# if not found, go to 
cd ~/fpga/esther_dma_ip_drivers/XDMA/linux-kernel/xdma
# compile driver and install
make clean
make
sudo make install
depmod -a
modprobe xdma
lspci | grep Xi
``` 
3. Load fpga configuration.
 ```bash
cd ~/fpga/Vivado/2019.1/ad-ipfn-hdl/projects/fmcjesdadc1/kc705/xsct 
./xsct.sh -interactive upload_fpga.tcl # take ~ 2 minutes

... Setting PC to Program Start Address 0x80000000
Successfully downloaded /home/esther/fpga/Vivado/2019.1/ad-ipfn-hdl/projects/fmcjesdadc1/kc705/xsct/simpleImage.kc705_fmcjesdadc1
Info: MicroBlaze #0 (target 4) Running

``` 
4. Refresh Linux PCIe devices
 ```bash
cd ~/fpga/Vivado/2019.1/ad-ipfn-hdl/projects/fmcjesdadc1/kc705/xsct 
./xsct.sh -interactive upload_fpga.tcl # take ~ 2 minutes
lspci | grep Xi
sudo echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove
sudo echo 1 > /sys/bus/pci/rescan
lspci | grep Xi
``` 
5. Test CLI app 
 ```bash
cd ~/fpga/esther_dma_ip_drivers/XDMA/linux-kernel/tools
./estherdaq  -a 0x2328fe0c -b 0x1f4dcd8 -c 0x2328fe0c -s 0x800000 -m 0x31999 -t
 ```
 6. Run GUI 
 ```bash
ssh -X esther@acis.local
cd ~/fpga/esther_dma_ip_drivers/XDMA/linux-kernel/tools
 ```



