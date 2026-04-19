"""
transform.py — move, scale, rotate elements; boolean operations
"""

from lxml import etree
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
import subprocess
import shutil


def transform_element(
    svg_path: str,
    element_id: str,
    translate: list = None,
    scale: list = None,
    rotate: float = None
) -> dict:
    """Apply transform to an element by ID."""
    path = Path(svg_path)
    if not path.exists():
        return {"error": f"SVG not found: {svg_path}"}

    tree = etree.parse(str(path))
    root = tree.getroot()

    el = None
    for candidate in root.iter():
        if candidate.get("id") == element_id:
            el = candidate
            break

    if el is None:
        return {"error": f"Element not found: {element_id}"}

    parts = []
    if translate:
        x, y = translate[0], translate[1] if len(translate) > 1 else 0
        parts.append(f"translate({x},{y})")
    if scale:
        if len(scale) == 1:
            parts.append(f"scale({scale[0]})")
        else:
            parts.append(f"scale({scale[0]},{scale[1]})")
    if rotate is not None:
        parts.append(f"rotate({rotate})")

    if parts:
        existing = el.get("transform", "")
        new_transform = " ".join(parts)
        el.set("transform", f"{existing} {new_transform}".strip())

    tree.write(str(path), pretty_print=True, xml_declaration=True, encoding="UTF-8")

    return {
        "status": "ok",
        "element_id": element_id,
        "transform": el.get("transform")
    }


def boolean_op(
    svg_path: str,
    id_a: str,
    id_b: str,
    operation: str,
    result_id: str
) -> dict:
    """
    Boolean operation via Inkscape CLI --actions.
    Operations: union, difference, intersection, exclusion
    """
    if not shutil.which("inkscape"):
        return {"error": "inkscape not found"}

    if not Path(svg_path).exists():
        return {"error": f"SVG not found: {svg_path}"}

    op_map = {
        "union": "path-union",
        "difference": "path-difference",
        "intersection": "path-intersection",
        "exclusion": "path-exclusion"
    }

    inkscape_op = op_map.get(operation)
    if not inkscape_op:
        return {"error": f"Unknown operation: {operation}"}

    # Select both elements, run boolean op, set result ID
    actions = (
        f"select-by-id:{id_a};"
        f"select-by-id:{id_b};"
        f"{inkscape_op};"
        f"object-set-attribute:id,{result_id};"
        f"file-save;"
        f"quit"
    )

    cmd = ["inkscape", svg_path, f"--actions={actions}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    return {
        "status": "ok",
        "operation": operation,
        "inputs": [id_a, id_b],
        "result_id": result_id
    }
