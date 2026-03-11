"""
Here's a Python class for working with HDF5 files:

```python
"""

import h5py
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class EstherHDF5Handler:
    """Handler for HDF5 file operations: create, open, import, and extract data."""

    def __init__(self, filepath: Union[str, Path], mode: str = "r"):
        """
        Args:
            filepath: Path to HDF5 file
            mode: 'r' (read), 'r+' (read/write), 'w' (create/truncate),
                  'x' (create/fail if exists), 'a' (read/write/create)
        """
        self.filepath = Path(filepath)
        self.mode = mode
        self._file: Optional[h5py.File] = None

    def __enter__(self):
        self._file = h5py.File(self.filepath, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def file(self) -> h5py.File:
        if self._file is None:
            raise RuntimeError("File not open. Use context manager or call open().")
        return self._file

    def open(self, mode: Optional[str] = None) -> h5py.File:
        """Manually open file (prefer using context manager)."""
        self._file = h5py.File(self.filepath, mode or self.mode)
        return self._file

    def close(self):
        """Close the HDF5 file."""
        if self._file:
            self._file.close()
            self._file = None

    # --- Dataset Operations ---

    def create_dataset(
        self,
        name: str,
        data: np.ndarray,
        attrs: Optional[Dict[str, Any]] = None,
        compression: Optional[str] = "gzip",
        chunks: bool = True,
    ) -> h5py.Dataset:
        """Create a dataset with optional attributes and compression."""
        dataset = self.file.create_dataset(
            name, data=data, compression=compression, chunks=chunks
        )
        if attrs:
            for key, value in attrs.items():
                dataset.attrs[key] = value
        return dataset

    def get_dataset(self, name: str) -> np.ndarray:
        """Get dataset as numpy array."""
        return self.file[name][:]

    def get_binary_data(self, name: str) -> bytes:
        """Get dataset as raw binary data."""
        return self.file[name][:].tobytes()

    # --- Attribute Operations ---

    def get_attrs(self, path: str = "/") -> Dict[str, Any]:
        """Get all attributes from a dataset or group."""
        obj = self.file if path == "/" else self.file[path]
        return dict(obj.attrs)

    def set_attrs(self, attrs: Dict[str, Any], path: str = "/"):
        """Set attributes on a dataset or group."""
        obj = self.file if path == "/" else self.file[path]
        for key, value in attrs.items():
            obj.attrs[key] = value

    def get_attr(self, key: str, path: str = "/") -> Any:
        """Get a single attribute value."""
        obj = self.file if path == "/" else self.file[path]
        return obj.attrs[key]

    # --- Group Operations ---

    def create_group(
        self, name: str, attrs: Optional[Dict[str, Any]] = None
    ) -> h5py.Group:
        """Create a group with optional attributes."""
        group = self.file.create_group(name)
        if attrs:
            for key, value in attrs.items():
                group.attrs[key] = value
        return group

    # --- Import/Export ---

    def import_from_dict(self, data: Dict[str, Any], group_path: str = "/"):
        """Import nested dictionary structure into HDF5."""
        group = self.file if group_path == "/" else self.file[group_path]

        attrs = {}
        for key, value in data.items():
            if key.startswith("@"):
                attrs[key[1:]] = value
            elif isinstance(value, dict):
                subgroup = group.create_group(key)
                self.import_from_dict(value, f"{group_path.rstrip('/')}/{key}")
            elif isinstance(value, (np.ndarray, list)):
                arr = np.array(value) if isinstance(value, list) else value
                group.create_dataset(key, data=arr, compression="gzip")
            else:
                attrs[key] = value

        for key, value in attrs.items():
            group.attrs[key] = value

    def export_to_dict(self, path: str = "/") -> Dict[str, Any]:
        """Export HDF5 structure to nested dictionary."""
        obj = self.file if path == "/" else self.file[path]
        result = {}

        for key, value in obj.attrs.items():
            result[f"@{key}"] = value

        if isinstance(obj, (h5py.File, h5py.Group)):
            for key in obj.keys():
                item = obj[key]
                if isinstance(item, h5py.Dataset):
                    result[key] = item[:]
                elif isinstance(item, h5py.Group):
                    result[key] = self.export_to_dict(f"{path.rstrip('/')}/{key}")

        return result

    # --- Inspection ---

    def list_contents(self, path: str = "/", recursive: bool = True) -> List[str]:
        """List all datasets and groups."""
        contents = []
        obj = self.file if path == "/" else self.file[path]

        def visitor(name, item):
            prefix = "D" if isinstance(item, h5py.Dataset) else "G"
            contents.append(f"[{prefix}] {name}")

        if recursive:
            obj.visititems(visitor)
        else:
            for key in obj.keys():
                item = obj[key]
                prefix = "D" if isinstance(item, h5py.Dataset) else "G"
                contents.append(f"[{prefix}] {key}")

        return contents

    def get_dataset_info(self, name: str) -> Dict[str, Any]:
        """Get metadata about a dataset."""
        ds = self.file[name]
        return {
            "shape": ds.shape,
            "dtype": str(ds.dtype),
            "size": ds.size,
            "nbytes": ds.nbytes,
            "compression": ds.compression,
            "chunks": ds.chunks,
            "attrs": dict(ds.attrs),
        }

    def list_all_attrs(self, path: str = "/") -> Dict[str, Dict[str, Any]]:
        """List all attributes from all groups and datasets in the file.

        Returns:
            Dict mapping paths to their attributes.
        """
        all_attrs = {}

        # Root attributes
        root_attrs = dict(self.file.attrs)
        if root_attrs:
            all_attrs["/"] = root_attrs

        # Visitor function for all items
        def visitor(name, item):
            item_attrs = dict(item.attrs)
            if item_attrs:
                all_attrs[f"/{name}"] = item_attrs

        self.file.visititems(visitor)
        return all_attrs


# --- Usage Examples ---

if __name__ == "__main__":
    # Create and write (mode='w' creates the file)
    with EstherHDF5Handler("example.h5", mode="w") as h5:
        # Create dataset with attributes
        data = np.random.rand(100, 100).astype(np.float32)
        h5.create_dataset(
            "measurements/temperature",
            data=data,
            attrs={"unit": "celsius", "sensor_id": 42},
        )

        # Import from dictionary
        h5.import_from_dict(
            {
                "@version": "1.0",
                "@author": "Bernardo",
                "experiment": {
                    "@date": "2025-05-21",
                    "readings": [1.0, 2.0, 3.0, 4.0],
                },
            }
        )

    # Read back (mode='r' is default)
    with EstherHDF5Handler("example.h5", mode="r") as h5:
        print("Contents:")
        for item in h5.list_contents():
            print(f"  {item}")

        temp_data = h5.get_dataset("measurements/temperature")
        print(f"\nTemperature shape: {temp_data.shape}")

        attrs = h5.get_attrs("measurements/temperature")
        print(f"Attributes: {attrs}")

        binary = h5.get_binary_data("experiment/readings")
        print(f"Binary size: {len(binary)} bytes")
        all_attributes = h5.list_all_attrs()

        for path, attrs in all_attributes.items():
            print(f"\n{path}:")
            for key, value in attrs.items():
                print(f"  {key}: {value}")
"""
```

**Key features:**

- **Context manager support** — use with `with` statements for automatic cleanup
- **Binary data extraction** — `get_binary_data()` returns raw bytes
- **Attribute handling** — get/set on any dataset or group
- **Dictionary import/export** — convert between nested dicts and HDF5 structure
- **Compression** — gzip by default, configurable
- **Inspection tools** — list contents, get dataset metadata

**Install dependency:**
```bash
pip install h5py numpy
```
"""
