Esther HFD5 Data Acquisition Files in AFS Storage
==============================

1. Install AFS client on your local machine, and connect to `/afs/psi.ch/project/esther`  
Installing and configuring tecnicoi server
[OpenAFS](https://si.tecnico.ulisboa.pt/en/servicos/armazenamento-e-backup/armazenamento-afs/instalacao-e-configuracao-do-openafs-em-linux-e-mac-os/) in Linux and Mac OS.

* Instructions for Linux (Debian 12.13):

```bash
sudo apt install linux-headers-amd64 openafs-modules-dkms
sudo apt install openafs-krb5 openafs-client (fill AFS cell with ist.utl.pt)
sudo apt-get install krb5-user (fill the default domain with IST.UTL.PT)
```

* reboot
* Obtain an AFS token an access the data:

```bash
kinit istxxxxx
aklog
tokens
cd /afs/ist.utl.pt/groups/esther
ls -alt
fs listacl ./ (show access control lists)
fs listquota -human
```

2. Plotting the data with Python

```python
cd ~/git-repos/esther-ops/hdf5
python3 plot_hdf5.py -h
python3 plot_hdf5.py -s -f /afs/ist.utl.pt/groups/esther/HDF5/316/data_with_metadata.h5
```

3. The HDF5 file is organized in groups and datasets. File contains the following subgroups and datasets:

HFD5 Structure:
> [G] cal-data
> [G] experiment
> [D] experiment/readings
> [G] raw-data
> [G] raw-data/cc
> [G] raw-data/cc/kistler
> [D] raw-data/cc/kistler/red-pitaya
> [D] raw-data/cc/kistler/rohde-schwarz
> [G] raw-data/ct
> [G] raw-data/dt
> [G] raw-data/st
>/:
>  author: Bernardo
>  created_date: 2026-04-09 15:14:29.934634
>  institution: IPFN-HPL Lab
>  title: Esther ST Experiment Data
>  version: 1.0
>
>/experiment:
>  date: 2026-04-09_13-29-09
>  fill_pressure: 24.83
>  name: H-2
>/raw-data:
>  description: Raw Data from instruments in binary
>/raw-data/cc:
>  description: Combustion Chamber
>/raw-data/cc/kistler:
>  description: CC Pressure Kistler Sensor
>  range: 250.0
>/raw-data/cc/kistler/red-pitaya:
>  channels: 1
>  decimation: 16
>  has_time: False
>  sampling_rate: 125000000.0
>  time_offset: -0.08119643479585648
>  unit: lsb
>/raw-data/cc/kistler/rohde-schwarz:
>  channels: 1
>  has_time: True
>  unit: volt

>/raw-data/ct:
>  description: Compression Tube Section
>/raw-data/dt:
>  description: Dump Tank Section
>/raw-data/st:
>  description: Shock Tube Section
4. To Build the HDF5 file, and import content of CSV data files execute the steps, sequentially:
  * Convert red-pitaya bin files to csv [../README.md#automated-pulse-trigger-and--data-acquisition-sequence](convert_tool)
  * ```bash
python3 build_hdf5.py -h
python3 build_hdf5.py -i -e "H-2" -d "2026-04-09_13-29-09" -k 250 -l 24.83 
python3 build_hdf5.py --pitaya  -f ~/git-repos/esther-ops/red-pitaya/data-files/data_file_2026-04-09_12-29-09.csv
python3 build_hdf5.py --schwarz  -f ~/Documents/Data-files/RS_ControlRoom/H_2/WFM01.CSV
# Explore file with:
python3 plot_kistler.py -e -f data_with_metadata.h5
```

5. Copy the hdf5 to AFS filesystem
```bash
mkdir /afs/ist.utl.pt/groups/esther/HDF5/318
cp data_with_metadata.h5 /afs/ist.utl.pt/groups/esther/HDF5/318/
```
6. Plot the Kistler data with matplotlib

```bash
# read file from AFS
python3 plot_kistler.py -a -r 318
```
