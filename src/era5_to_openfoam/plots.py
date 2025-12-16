"""Plotting utilities for ERA5-derived diagnostics."""

from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import xarray as xr

from .analysis import extract_profile_at_time


STYLE = {
    "linewidth": 1.8,
    "alpha": 0.9,
}


def _prepare_output_path(output_dir: Path, filename: str) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename


def plot_wind_timeseries(single_level: xr.Dataset, output_dir: Path, *, filename: str = "wind_timeseries.png") -> Path:
    """Plot time series of 10 m wind speed."""

    if "wind_speed_10m" not in single_level:
        raise KeyError("Expected 'wind_speed_10m' in single-level diagnostics")

    fig, ax = plt.subplots(figsize=(9, 4))
    single_level["wind_speed_10m"].plot(ax=ax, **STYLE)
    ax.set_ylabel("Wind speed (m s$^{-1}$)")
    ax.set_title("ERA5 10 m wind speed")
    ax.grid(True, linestyle=":", alpha=0.6)

    output_path = _prepare_output_path(output_dir, filename)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_heat_flux_timeseries(single_level: xr.Dataset, output_dir: Path, *, filename: str = "heat_flux.png") -> Optional[Path]:
    """Plot net surface heat flux if present."""

    if "net_surface_heat_flux" not in single_level:
        return None

    fig, ax = plt.subplots(figsize=(9, 4))
    single_level["net_surface_heat_flux"].plot(ax=ax, **STYLE)
    ax.set_ylabel("Net surface heat flux (W m$^{-2}$)")
    ax.set_title("ERA5 net surface heat flux")
    ax.grid(True, linestyle=":", alpha=0.6)

    output_path = _prepare_output_path(output_dir, filename)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_vertical_profiles(
    profiles: xr.Dataset,
    output_dir: Path,
    *,
    timestamp=None,
    filename: str = "profiles.png",
    fields: Optional[Iterable[str]] = None,
) -> Path:
    """Plot vertical profiles of wind speed and potential temperature at a specific time."""

    if timestamp is None:
        timestamp = profiles.time.values[0]

    available_fields = fields or ["wind_speed", "theta"]
    profile_at_time = extract_profile_at_time(profiles, timestamp)

    fig, ax = plt.subplots(1, len(available_fields), figsize=(11, 5), sharey=True)
    if len(available_fields) == 1:
        ax = [ax]

    for axis, field in zip(ax, available_fields):
        if field not in profile_at_time:
            continue
        values, levels = profile_at_time[field]
        axis.plot(values, levels, label=field, **STYLE)
        axis.set_xlabel(field.replace("_", " "))
        axis.invert_yaxis()
        axis.grid(True, linestyle=":", alpha=0.6)
        axis.legend()

    ax[0].set_ylabel("Pressure level (hPa)")
    fig.suptitle(f"ERA5 profile at {str(timestamp)}")

    output_path = _prepare_output_path(output_dir, filename)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path
