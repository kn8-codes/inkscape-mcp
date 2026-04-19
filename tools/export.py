"""
export.py — render SVG to PNG or clean SVG via Inkscape CLI
"""

import subprocess
import shutil
from pathlib import Path


def _inkscape_available() -> bool:
    return shutil.which("inkscape") is not None


def export_png(
    svg_path: str,
    output_path: str,
    width: int = None,
    height: int = None,
    dpi: int = 96
) -> dict:
    """Render SVG to PNG using Inkscape CLI."""
    if not _inkscape_available():
        return {"error": "inkscape not found — install via: brew install inkscape"}

    if not Path(svg_path).exists():
        return {"error": f"SVG not found: {svg_path}"}

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = ["inkscape", svg_path, f"--export-filename={output_path}"]

    if width:
        cmd.append(f"--export-width={width}")
    if height:
        cmd.append(f"--export-height={height}")

    cmd.append(f"--export-dpi={dpi}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {"error": result.stderr.strip(), "cmd": " ".join(cmd)}

    return {
        "status": "ok",
        "input": svg_path,
        "output": output_path,
        "dpi": dpi
    }


def export_svg_clean(
    svg_path: str,
    output_path: str
) -> dict:
    """
    Export a clean SVG — strips Inkscape editor metadata,
    preserves all IDs so GSAP can address them.
    Uses inkscape --export-plain-svg.
    """
    if not _inkscape_available():
        return {"error": "inkscape not found — install via: brew install inkscape"}

    if not Path(svg_path).exists():
        return {"error": f"SVG not found: {svg_path}"}

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "inkscape",
        svg_path,
        "--export-plain-svg",
        f"--export-filename={output_path}"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    return {
        "status": "ok",
        "input": svg_path,
        "output": output_path
    }
