Esther HFD5 Data Acquisition Files in NFS Storage
==============================

1. Install  SSHFS client on your local machine, and connect to  server  
* Instructions for Linux (Debian 12.13):

```bash
sudo apt update
sudo apt install sshfs
cd ~/git-repos/esther-ops/hdf5
mkdir hdf-files
sshfs -o ro,default_permissions,cache=yes fumanchu.tecnico.ulisboa.pt:/srv/nfs/shared/hdf-files ./hdf-files
```


2. Plotting the data with Python
 * Plot CC Kistler data
```python
cd ~/git-repos/esther-ops/hdf5
python3 plot_kistler_cc.py -f hdf-files/318/data_with_metadata.h5  
```

 * Plot Bunker Rohde-schwarz oscilloscope  data
```python
python3 plot_rohde_bunker.py -f hdf-files/318/data_with_metadata.h5
```
3. The HDF5 file is organized in groups and datasets. File contains the following subgroups and datasets:

HFD5 Structure:
```
```
```
$ init_hdf.py -x
> HDF5 File Content:
> [G] cal-data
> [G] diagnostics
> [G] diagnostics/control-room
> [G] diagnostics/experimental-hall
> [G] diagnostics/experimental-hall/cc
> [G] diagnostics/experimental-hall/cc/kistler
> [G] diagnostics/experimental-hall/ct
> [G] diagnostics/experimental-hall/ct/kistler
> [G] diagnostics/experimental-hall/dt
> [G] diagnostics/experimental-hall/st
> [G] experiment
> [G] header
> [G] raw-data
> [G] raw-data/control-room
> [G] raw-data/control-room/red-pitaya
> [G] raw-data/control-room/red-pitaya/metadata
> [G] raw-data/control-room/red-pitaya/waveforms
> [D] raw-data/control-room/red-pitaya/waveforms/CH1
> [G] raw-data/control-room/rohde-schwarz
> [G] raw-data/control-room/rohde-schwarz/metadata
> [G] raw-data/control-room/rohde-schwarz/waveforms
> [D] raw-data/control-room/rohde-schwarz/waveforms/C1
> [D] raw-data/control-room/rohde-schwarz/waveforms/TIME
> [G] raw-data/experimental-hall
> [G] raw-data/experimental-hall/rohde-schwarz
> [G] raw-data/experimental-hall/rohde-schwarz/metadata
> [G] raw-data/experimental-hall/rohde-schwarz/waveforms
> [D] raw-data/experimental-hall/rohde-schwarz/waveforms/C1
> [D] raw-data/experimental-hall/rohde-schwarz/waveforms/C2
> [D] raw-data/experimental-hall/rohde-schwarz/waveforms/C3
> [D] raw-data/experimental-hall/rohde-schwarz/waveforms/C4
> [D] raw-data/experimental-hall/rohde-schwarz/waveforms/TIME
> [G] raw-data/experimental-hall/tektronix
> [G] raw-data/experimental-hall/tektronix/metadata
> [G] raw-data/experimental-hall/tektronix/waveforms
> [D] raw-data/experimental-hall/tektronix/waveforms/CH1
> [D] raw-data/experimental-hall/tektronix/waveforms/CH2
> [D] raw-data/experimental-hall/tektronix/waveforms/TIME

/diagnostics:
  description: Sensors/instruments

/diagnostics/control-room:
  description: Sensors in HPL Control room

/diagnostics/experimental-hall:
  description: Sensors/instruments in HPL experimental hall

/diagnostics/experimental-hall/cc:
  description: Combustion Chamber

/diagnostics/experimental-hall/cc/kistler:
  amplifier: Kistler Type 5015
  data_key_0: raw-data/control-room/rohde-schwarz/waveforms/C1
  data_key_1: raw-data/control-room/red-pitaya/waveforms/CH1
  description: CC Pressure Kistler Sensor
  pressure_range: 250.0
  wire_number: 504

/diagnostics/experimental-hall/ct:
  description: Compression Tube Section

/diagnostics/experimental-hall/ct/kistler:
  amplifier: Kistler Type 5015
  data_key_0: raw-data/experimental-hall/rohde-schwarz/waveforms/C1
  data_key_1: raw-data/experimental-hall/tektronix/waveforms/CH1
  description: CC Pressure Kistler Sensor
  pressure_range: 10.0
  wire_number: 501

/diagnostics/experimental-hall/dt:
  description: Dump Tank Section

/diagnostics/experimental-hall/st:
  description: Shock Tube Section

/experiment:
  cc_fill_pressure: 24.83
  date: 2026-04-09_13-29-09
  he_h2_o2_ratios: [8.  2.  1.2]
  name: H-2
/header:
  author: bernardo.carvalho@tecnico.ulisboa.pt
  created_date: 2026-05-05 13:26:36.302320
  institution: IPFN-HPL Lab
  title: Esther ST Experiment Data
  version: 1.0

/raw-data:
  description: Raw Data from instruments in binary
/raw-data/control-room:
  description: Instruments in HPL Control room
/raw-data/control-room/red-pitaya/metadata:
  channels: 1
  decimation: 16
  ecosystem: 1.04-93661995d
  has_time: False
  hostname: rp-f01735.local
  model: STEMlab 125-14
  sample_rate: 125000000.0
  time_offset: -0.08119643233163071
  unit: lsb
  vertical_range: +-1V
/raw-data/control-room/rohde-schwarz/metadata:
  firmware_version: 02.400
  has_time: True
  model: rtb2004
  serial_number: 1333.1005k04/107554
  unit: V
  vertical_scale: Volt
/raw-data/control-room/rohde-schwarz/waveforms:
  columns: ['TIME' 'C1']
  num_samples: 10000000
  source_file: WFM01.CSV
/raw-data/control-room/rohde-schwarz/waveforms/C1:
  unit: V
/raw-data/control-room/rohde-schwarz/waveforms/TIME:
  unit: s
/raw-data/experimental-hall:
  description: Instruments in HPL experimental hall
/raw-data/experimental-hall/rohde-schwarz/metadata:
  firmware_version: 02.400
  has_time: True
  model: rtb2004
  serial_number: 1333.1005k04/207766
  unit: V
  vertical_scale: Volt
/raw-data/experimental-hall/rohde-schwarz/waveforms:
  columns: ['TIME' 'C1' 'C2' 'C3' 'C4']
  num_samples: 7500060
  source_file: WFM04.CSV
/raw-data/experimental-hall/rohde-schwarz/waveforms/C1:
  unit: V
/raw-data/experimental-hall/rohde-schwarz/waveforms/C2:
  unit: V
/raw-data/experimental-hall/rohde-schwarz/waveforms/C3:
  unit: V
/raw-data/experimental-hall/rohde-schwarz/waveforms/C4:
  unit: V
/raw-data/experimental-hall/rohde-schwarz/waveforms/TIME:
  unit: s
/raw-data/experimental-hall/tektronix/metadata:
  firmware_version: 3.18
  has_time: True
  model: MDO4104B-3
  serial_number: C020372
  unit: V
  vertical_scale: Volt
/raw-data/experimental-hall/tektronix/waveforms/CH1:
  unit: V
/raw-data/experimental-hall/tektronix/waveforms/CH2:
  unit: V
/raw-data/experimental-hall/tektronix/waveforms/TIME:
  unit: s



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
```
4. To Build the HDF5 file, and import content of CSV data files execute the steps, sequentially:
  * Convert red-pitaya bin files to csv [../README.md#automated-pulse-trigger-and--data-acquisition-sequence](convert_tool)
  * Run
```bash
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
