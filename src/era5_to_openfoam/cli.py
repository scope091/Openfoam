"""Command-line entry point for ERA5 to OpenFOAM conversion."""

from argparse import ArgumentParser
from pathlib import Path

import xarray as xr

from .analysis import (
    compute_bulk_richardson_number,
    compute_pressure_level_profiles,
    compute_single_level_metrics,
    stability_label,
)
from .data_loader import load_pressure_level_dataset, load_single_level_dataset
from .openfoam_export import write_openfoam_boundary_table, write_openfoam_initial_conditions
from .plots import plot_heat_flux_timeseries, plot_vertical_profiles, plot_wind_timeseries


SECONDS_PER_HOUR = 3600


def _parse_args():
    parser = ArgumentParser(description="Process ERA5 datasets and export OpenFOAM inputs.")
    parser.add_argument("single_level", type=Path, help="Path to ERA5 single-level NetCDF file")
    parser.add_argument("pressure_level", type=Path, help="Path to ERA5 pressure-level NetCDF file")
    parser.add_argument("output", type=Path, help="Output directory for plots and OpenFOAM files")
    parser.add_argument("--levels", nargs="*", type=int, help="Optional list of pressure levels to keep (hPa)")
    parser.add_argument("--time-start", type=str, help="Start time for subsetting (YYYY-mm-dd HH:MM)")
    parser.add_argument("--time-end", type=str, help="End time for subsetting (YYYY-mm-dd HH:MM)")
    return parser.parse_args()


def _time_slice(args):
    if args.time_start and args.time_end:
        return slice(args.time_start, args.time_end)
    if args.time_start:
        return slice(args.time_start, None)
    if args.time_end:
        return slice(None, args.time_end)
    return None


def main():
    args = _parse_args()
    time_slice = _time_slice(args)

    single = load_single_level_dataset(args.single_level, time_slice=time_slice)
    pressure = load_pressure_level_dataset(args.pressure_level, levels=args.levels, time_slice=time_slice)

    single_metrics = compute_single_level_metrics(single)
    profiles = compute_pressure_level_profiles(pressure)

    # Compute a bulk Richardson number using bottom (lowest pressure level) and next level
    bottom = profiles.isel(level=-1)
    top = profiles.isel(level=-2)
    if "z" in pressure:
        delta_z = float(abs(pressure["z"].isel(level=-2) - pressure["z"].isel(level=-1)))
    else:
        # Approximate separation with pressure scale height assumption
        delta_z = 150.0

    ri = compute_bulk_richardson_number(
        bottom["theta"],
        top["theta"],
        bottom["wind_speed"],
        top["wind_speed"],
        delta_z,
    )
    single_metrics["stability"] = stability_label(ri)

    args.output.mkdir(parents=True, exist_ok=True)
    plot_wind_timeseries(single_metrics, args.output)
    plot_heat_flux_timeseries(single_metrics, args.output)
    plot_vertical_profiles(profiles, args.output)

    # Export OpenFOAM friendly tables
    write_openfoam_boundary_table(bottom["wind_speed"].values, args.output, field="U")
    write_openfoam_boundary_table(bottom["theta"].values, args.output, field="T")
    write_openfoam_initial_conditions(profiles, args.output, rename={"wind_speed": "U", "theta": "T"})

    print(f"Processed datasets saved to {args.output}")


if __name__ == "__main__":
    main()
