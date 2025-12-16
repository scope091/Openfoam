# ERA5 to OpenFOAM utilities

This repository contains a small Python toolkit for turning ERA5 single-level and pressure-level NetCDF files into OpenFOAM-friendly inputs while producing quick-look atmospheric stability plots.

## Features
- Load single-level and pressure-level ERA5 products with `xarray`.
- Derive key diagnostics: wind speed, potential temperature, simple surface heat flux, and bulk Richardson number for stability.
- Plot wind speed, surface heat flux, and vertical profiles.
- Export vertical profiles to OpenFOAM dictionary files and tabulated boundary profiles.

## Getting started
1. Install dependencies (Python 3.10+ recommended):

   ```bash
   pip install xarray netCDF4 matplotlib numpy pandas
   ```

2. Run the CLI:

   ```bash
   python -m era5_to_openfoam.cli ERA5_single_level.nc ERA5_pressure_level.nc outputs/ \
     --levels 1000 925 850 --time-start "2024-01-01" --time-end "2024-01-02"
   ```

   The command generates plots in `outputs/` and writes OpenFOAM field files (`U`, `T`) plus tabulated profiles (`U_profile.dat`, `T_profile.dat`).

## Library usage example

```python
from pathlib import Path
from era5_to_openfoam import (
    load_pressure_level_dataset,
    load_single_level_dataset,
    compute_single_level_metrics,
    compute_pressure_level_profiles,
    write_openfoam_initial_conditions,
    plot_vertical_profiles,
)

single = load_single_level_dataset(Path("ERA5_single_level.nc"))
pressure = load_pressure_level_dataset(Path("ERA5_pressure_level.nc"), levels=[1000, 925, 850])
metrics = compute_single_level_metrics(single)
profiles = compute_pressure_level_profiles(pressure)

write_openfoam_initial_conditions(profiles, Path("outputs"), rename={"wind_speed": "U", "theta": "T"})
plot_vertical_profiles(profiles, Path("outputs"))
```
