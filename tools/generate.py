"""
generate.py — svg_from_description and add_shape
Outputs GSAP-ready SVG: named IDs, clean groups, no inline transforms on root
"""

from lxml import etree
from pathlib import Path
import re

SVG_NS = "http://www.w3.org/2000/svg"
NSMAP = {None: SVG_NS}


def _make_svg(width: int, height: int) -> etree._Element:
    """Create a base SVG element following the animation-ready contract."""
    svg = etree.Element("svg", nsmap=NSMAP)
    svg.set("id", "root")
    svg.set("viewBox", f"0 0 {width} {height}")
    svg.set("width", str(width))
    svg.set("height", str(height))
    svg.set("xmlns", SVG_NS)
    return svg


def generate_svg(
    brief: str,
    output_path: str,
    width: int = 800,
    height: int = 600
) -> dict:
    """
    Generate a structured SVG from a creative brief.
    This is the stub — agent describes shapes, we build the SVG.
    Real implementation: parse brief into shape descriptors, render each.
    For now: returns a valid GSAP-ready SVG skeleton with a comment.
    """
    svg = _make_svg(width, height)

    # Base layer group — agent populates this
    layer = etree.SubElement(svg, "g")
    layer.set("id", "layer-1")
    layer.set("class", "layer")

    # Comment preserving the brief for reference
    comment = etree.Comment(f" brief: {brief} ")
    layer.append(comment)

    # Write output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    tree = etree.ElementTree(svg)
    tree.write(
        str(output),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )

    return {
        "status": "ok",
        "path": str(output),
        "width": width,
        "height": height,
        "layers": ["layer-1"],
        "brief": brief
    }


def add_shape(
    svg_path: str,
    shape: str,
    attrs: dict,
    id: str,
    group: str = None
) -> dict:
    """Add a shape element to an existing SVG."""
    path = Path(svg_path)
    if not path.exists():
        return {"error": f"SVG not found: {svg_path}"}

    tree = etree.parse(str(path))
    root = tree.getroot()

    # Strip namespace for easier xpath
    def find_by_id(element_id: str):
        # Try with and without namespace
        results = root.findall(f'.//*[@id="{element_id}"]')
        return results[0] if results else None

    # Find parent group
    if group:
        parent = find_by_id(group)
        if parent is None:
            return {"error": f"Group not found: {group}"}
    else:
        # Default to first layer
        parent = root.find(f"{{{SVG_NS}}}g")
        if parent is None:
            parent = root

    # Create shape element
    el = etree.SubElement(parent, f"{{{SVG_NS}}}{shape}")
    el.set("id", id)

    # Apply attributes
    for key, val in attrs.items():
        el.set(key, str(val))

    tree.write(
        str(path),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )

    return {
        "status": "ok",
        "shape": shape,
        "id": id,
        "parent": group or "layer-1"
    }
