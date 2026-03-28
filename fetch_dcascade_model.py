"""
Fetch core model files from the dcascade-py v2.0.0 upstream release.

These files are identical to the upstream release and are not stored in this
repository.  Run this script once after cloning, or after a clean checkout,
before running tests or the plugin.

Usage:
    python fetch_dcascade_model.py
"""

import sys
import urllib.error
import urllib.request
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from io import BytesIO

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------

# Official GitHub release archive for dcascade-py v2.0.0.
# This URL is a trusted, pinned release from the upstream project repository.
UPSTREAM_RELEASE_URL = (
    "https://github.com/dcascade-py/dcascade-py/archive/refs/tags/v2.0.0.zip"
)

# The prefix inside the zip archive for the upstream src/ files.
UPSTREAM_SRC_PREFIX = "dcascade-py-2.0.0/src/"

# Files that are taken verbatim from the upstream release.
UPSTREAM_FILES = [
    "GSD_curvefit.py",
    "cascade.py",
    "constants.py",
    "d_finder.py",
    "flow_depth.py",
    "plot_function.py",
    "preprocessing.py",
    "reach_data.py",
    "slope_reduction.py",
    "transport_capacity_calculator.py",
    "width_variation.py",
    "widget.py",
]

# Destination inside this repository.
DEST_DIR = Path(__file__).parent / "qgis_plugin" / "src"


def _download_zip(url: str) -> bytes:
    print(f"Downloading {url} …")
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error while downloading the upstream release archive.\n"
            f"  URL: {url}\n"
            f"  Cause: {exc.reason}\n"
            "Check your internet connection and try again."
        ) from exc
    print(f"  Downloaded {len(data):,} bytes.")
    return data


def fetch_model_files(force: bool = False) -> None:
    """Download the upstream model source files into qgis_plugin/src/.

    Parameters
    ----------
    force:
        Re-download and overwrite even if files already exist.
    """
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Check if all files are already present (skip download if so)
    missing = [f for f in UPSTREAM_FILES if not (DEST_DIR / f).exists()]
    if not missing and not force:
        print("All upstream model files are already present – nothing to do.")
        print("  (Pass --force to re-download them.)")
        return

    if missing:
        print(f"Missing {len(missing)} file(s): {', '.join(missing)}")

    zip_bytes = _download_zip(UPSTREAM_RELEASE_URL)

    try:
        zf_handle = ZipFile(BytesIO(zip_bytes))
    except BadZipFile as exc:
        raise RuntimeError(
            "The downloaded archive appears to be corrupted or incomplete.\n"
            "Delete any cached files and re-run this script."
        ) from exc

    with zf_handle as zf:
        # Collect available names for quick lookup
        names = set(zf.namelist())

        for filename in UPSTREAM_FILES:
            zip_path = UPSTREAM_SRC_PREFIX + filename
            if zip_path not in names:
                print(f"  WARNING: {zip_path} not found in archive – skipping.")
                continue

            dest = DEST_DIR / filename
            content = zf.read(zip_path)
            dest.write_bytes(content)
            print(f"  Extracted → {dest.relative_to(Path(__file__).parent)}")

    print("\nDone.  Upstream model files are ready.")


if __name__ == "__main__":
    force = "--force" in sys.argv
    try:
        fetch_model_files(force=force)
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\nUnexpected error: {exc}", file=sys.stderr)
        sys.exit(1)
