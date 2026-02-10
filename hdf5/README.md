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

```bash
kinit istxxxxx
aklog
tokens
cd /afs/ist.utl.pt/groups/esther
fs listacl ./ (show access control lists)
fs listquota -human
```

2. Plotting the data

```python
cd ~/git-repos/esther-ops/hdf5
python3 plot_hdf5.py -h
python3 plot_hdf5.py -s -f /afs/ist.utl.pt/groups/esther/HDF5/316/data_with_metadata.h5
```

3. The HDF5 file is organized in groups and datasets. File contains the following subgroups and datasets:

> Group: cal-data  
> Group: cal-data/cc  
> Group: cal-data/ct  
>Group: cal-data/dt  
>Group: cal-data/st  
>Group: raw-data  
>Group: raw-data/cc  
>Group: raw-data/cc/kistler  
>Dataset: raw-data/cc/kistler/red-pitaya, Shape: (16007168,), Dtype: int16  
>Dataset: raw-data/cc/kistler/rhode-schwarz, Shape: (2, 10000000), Dtype: float32  
>Group: raw-data/ct  
>Group: raw-data/dt  
>Group: raw-data/st  

* The Medata is stored in the attributes of the HDF5 file, and contains the following information:

> created_date: 2026-01-27 19:05:00.696462  
> experiment_name: S-116  
> institution: IPFN-HPL Lab  
> shot_date: 2025-12-23_17-44-44  
> title: Esther ST Experiment Data  
> version: 1.0  

* The Red Pitaya data is stored in the dataset `raw-data/cc/kistler/red-pitaya`, and contains the raw data acquired from the Red Pitaya oscilloscope. The dataset attributes are.

>Dataset 'red-pitaya' attributes:  
> channels: 1  
> description: CC Pressure Kistler Sensor red-pitaya data  
> file_path: /home/esther/git-repos/esther-ops/hdf5/data_with_metadata.h5  
> sampling_rate: 7812500.0  
> time_offset: 0.0  
> units: lsb  
> sampling_rate: 7812500.0  
>data.shape[0] 16007168  
>
