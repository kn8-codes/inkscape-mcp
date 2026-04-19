"""
batch.py — batch export all SVGs in a folder to PNG
"""

import subprocess
import shutil
from pathlib import Path


def batch_export_folder(
    input_folder: str,
    output_folder: str,
    width: int = None,
    height: int = None,
    dpi: int = 96
) -> dict:
    """Export all SVGs in input_folder to PNG in output_folder."""
    if not shutil.which("inkscape"):
        return {"error": "inkscape not found"}

    input_path = Path(input_folder)
    output_path = Path(output_folder)

    if not input_path.exists():
        return {"error": f"Input folder not found: {input_folder}"}

    output_path.mkdir(parents=True, exist_ok=True)

    svgs = list(input_path.glob("*.svg"))
    if not svgs:
        return {"error": f"No SVG files found in {input_folder}"}

    results = []
    errors = []

    for svg in svgs:
        out = output_path / (svg.stem + ".png")
        cmd = ["inkscape", str(svg), f"--export-filename={out}", f"--export-dpi={dpi}"]
        if width:
            cmd.append(f"--export-width={width}")
        if height:
            cmd.append(f"--export-height={height}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            results.append(str(out))
        else:
            errors.append({"file": str(svg), "error": result.stderr.strip()})

    return {
        "status": "ok" if not errors else "partial",
        "exported": len(results),
        "failed": len(errors),
        "outputs": results,
        "errors": errors
    }
