"""Data loading helpers for ERA5 single- and pressure-level products."""

from pathlib import Path
from typing import Iterable, Optional

import xarray as xr


def _open_dataset(path: Path) -> xr.Dataset:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return xr.open_dataset(path)


def load_single_level_dataset(path: Path, *, time_slice: Optional[slice] = None) -> xr.Dataset:
    """Load a single-level ERA5 NetCDF dataset.

    Parameters
    ----------
    path:
        Path to the NetCDF file that contains variables like ``u10`` and ``v10``.
    time_slice:
        Optional slice object to limit the time range (e.g. ``slice('2024-01-01', '2024-01-02')``).
    """

    ds = _open_dataset(path)
    if time_slice is not None:
        ds = ds.sel(time=time_slice)
    return ds


def load_pressure_level_dataset(
    path: Path, *, levels: Optional[Iterable[int]] = None, time_slice: Optional[slice] = None
) -> xr.Dataset:
    """Load an ERA5 pressure-level NetCDF dataset.

    Parameters
    ----------
    path:
        Path to the NetCDF file with pressure-level variables such as ``u``, ``v``, ``t``, and ``z``.
    levels:
        Optional iterable with the desired pressure levels (in hPa) to select.
    time_slice:
        Optional time subset applied after opening the dataset.
    """

    ds = _open_dataset(path)
    if levels is not None:
        ds = ds.sel(level=list(levels))
    if time_slice is not None:
        ds = ds.sel(time=time_slice)
    return ds
