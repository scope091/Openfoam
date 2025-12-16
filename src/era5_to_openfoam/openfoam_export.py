"""Write minimal OpenFOAM dictionaries from ERA5 diagnostics."""

from pathlib import Path
from typing import Dict, Iterable

import xarray as xr


HEADER = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2206                                 |
|   \\  /    A nd           | Web:      www.OpenFOAM.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}
"""


def _format_foamy_table(values: Iterable[float]) -> str:
    values = list(values)
    formatted = "".join(f"    ({v:.4f} 0 0)\n" for v in values)
    return f"{len(values)}\n(\n{formatted})\n"


def write_openfoam_boundary_table(values: Iterable[float], output_dir: Path, *, field: str = "U") -> Path:
    """Write a simple table of values usable by `setFields` or boundary conditions."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{field}_profile.dat"

    values = list(values)
    formatted = "\n".join(f"{i} {val:.4f}" for i, val in enumerate(values))
    path.write_text(formatted)
    return path


def write_openfoam_initial_conditions(
    profiles: xr.Dataset,
    output_dir: Path,
    *,
    timestamp=None,
    rename: Dict[str, str] | None = None,
) -> Dict[str, Path]:
    """Export vertical profiles to OpenFOAM field files.

    The function writes one file per field contained in ``profiles``. Each file follows
    the standard dictionary layout and uses a uniform value below the lowest supplied
    level and tabulated values above.
    """

    rename = rename or {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if timestamp is None:
        timestamp = profiles.time.values[0]

    profiles_at_time = profiles.sel(time=timestamp)
    written: Dict[str, Path] = {}

    for name, dataarray in profiles_at_time.data_vars.items():
        foam_name = rename.get(name, name)
        values = dataarray.values
        header = HEADER.replace("U", foam_name)
        body = _format_foamy_table(values)
        content = f"{header}\nnonuniform List<vector>\n{body}\nboundaryField\n{{\n}}\n"
        path = output_dir / foam_name
        path.write_text(content)
        written[foam_name] = path

    return written
