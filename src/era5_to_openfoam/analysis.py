"""Core analysis routines for atmospheric stability derived from ERA5."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import xarray as xr

KAPPA = 0.2854
P0 = 1000.0  # reference pressure in hPa
G = 9.81


def calculate_wind_speed(u: xr.DataArray, v: xr.DataArray) -> xr.DataArray:
    """Return horizontal wind-speed magnitude from U/V components."""

    return np.sqrt(u ** 2 + v ** 2)


def potential_temperature(temperature_k: xr.DataArray, pressure_hpa: xr.DataArray) -> xr.DataArray:
    """Convert temperature to potential temperature using the Poisson equation."""

    return temperature_k * (P0 / pressure_hpa) ** KAPPA


def compute_single_level_metrics(ds: xr.Dataset) -> xr.Dataset:
    """Compute basic fields (wind speed, potential temperature, surface buoyancy flux).

    Expects typical single-level ERA5 variables: ``u10`` and ``v10`` for wind components
    at 10 m, ``t2m`` for 2 m air temperature, ``ssr`` (surface net solar radiation) and
    ``strd`` (surface thermal radiation downwards). The function falls back gracefully
    when energy terms are missing.
    """

    derived = {}
    if {"u10", "v10"}.issubset(ds):
        derived["wind_speed_10m"] = calculate_wind_speed(ds["u10"], ds["v10"])
    if "t2m" in ds:
        derived["theta_2m"] = potential_temperature(ds["t2m"], pressure_hpa=ds["sp"] / 100.0 if "sp" in ds else P0)

    if "ssr" in ds and "strd" in ds:
        net_radiation = ds["ssr"] + ds["strd"]
        derived["net_surface_heat_flux"] = net_radiation.diff("time", label="lower", n=1)

    return xr.Dataset(derived)


def compute_pressure_level_profiles(ds: xr.Dataset) -> xr.Dataset:
    """Compute wind speed and potential temperature for each pressure level."""

    if not {"u", "v", "t", "level"}.issubset(ds):
        missing = {"u", "v", "t", "level"} - set(ds.data_vars) - set(ds.coords)
        raise KeyError(f"Dataset missing required variables: {missing}")

    wind_speed = calculate_wind_speed(ds["u"], ds["v"])
    theta = potential_temperature(ds["t"], ds["level"])

    return xr.Dataset({"wind_speed": wind_speed, "theta": theta})


def compute_bulk_richardson_number(
    theta_bottom: xr.DataArray,
    theta_top: xr.DataArray,
    wind_bottom: xr.DataArray,
    wind_top: xr.DataArray,
    delta_z: float,
) -> xr.DataArray:
    """Compute a bulk Richardson number using two levels.

    Parameters
    ----------
    theta_bottom, theta_top:
        Potential temperatures (K) at the lower and upper reference heights.
    wind_bottom, wind_top:
        Wind-speed magnitudes (m s-1) at the same two heights.
    delta_z:
        Vertical separation between the levels (m).
    """

    shear = (wind_top - wind_bottom) ** 2
    buoyancy_term = (theta_top - theta_bottom) / theta_bottom
    return (G * delta_z * buoyancy_term) / (shear + 1e-6)


def stability_label(richardson_number: xr.DataArray) -> xr.DataArray:
    """Classify stability from a Richardson number field."""

    bins = [-np.inf, 0.0, 0.25, np.inf]
    labels = ["unstable", "neutral", "stable"]
    return xr.apply_ufunc(
        lambda value: labels[int(np.digitize(value, bins)) - 1],
        richardson_number,
    )


def extract_profile_at_time(profiles: xr.Dataset, timestamp) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """Extract profile arrays (values, pressure levels) at a given timestamp."""

    if "level" not in profiles.coords:
        raise KeyError("Expected 'level' coordinate in profiles dataset")

    profile_at_time = profiles.sel(time=timestamp)
    return {
        name: (profile_at_time[name].values, profile_at_time["level"].values)
        for name in profiles.data_vars
    }
