"""
generate.py — svg_from_description and add_shape
Outputs GSAP-ready SVG: named IDs, clean groups, no inline transforms on root

Brief parser turns natural language into shape descriptors.
Default palette: BoomMates design tokens (brick red + cream + charcoal).
"""

from lxml import etree
from pathlib import Path
import re

SVG_NS = "http://www.w3.org/2000/svg"
NSMAP = {None: SVG_NS}

PALETTES = {
    "boommates": {
        "primary":    "#B8402A",
        "secondary":  "#F5EDE0",
        "dark":       "#241A10",
        "accent":     "#2D5A3D",
        "muted":      "#6B5A4E",
        "border":     "#D4C4B0",
        "surface":    "#FEFAF4",
        "amber":      "#C17F24",
    },
    "greymarket": {
        "primary":    "#E85D04",
        "secondary":  "#0D0F12",
        "dark":       "#0D0F12",
        "accent":     "#67E8F9",
        "muted":      "#6B7280",
        "border":     "#1F2937",
        "surface":    "#111318",
        "amber":      "#F59E0B",
    },
    "default": {
        "primary":    "#2563EB",
        "secondary":  "#F8FAFC",
        "dark":       "#0F172A",
        "accent":     "#7C3AED",
        "muted":      "#94A3B8",
        "border":     "#E2E8F0",
        "surface":    "#FFFFFF",
        "amber":      "#F59E0B",
    },
}

SHAPE_KEYWORDS = {
    "circle":     "circle",
    "dot":        "circle",
    "ball":       "circle",
    "bubble":     "circle",
    "rect":       "rect",
    "rectangle":  "rect",
    "box":        "rect",
    "square":     "rect",
    "card":       "rect",
    "panel":      "rect",
    "line":       "line",
    "bar":        "rect",
    "strip":      "rect",
    "ellipse":    "ellipse",
    "oval":       "ellipse",
    "pill":       "ellipse",
    "badge":      "ellipse",
    "triangle":   "polygon",
    "arrow":      "polygon",
    "diamond":    "polygon",
    "star":       "polygon",
    "path":       "path",
    "curve":      "path",
    "wave":       "path",
    "arc":        "path",
    "text":       "text",
    "label":      "text",
    "heading":    "text",
    "title":      "text",
    "caption":    "text",
    "copy":       "text",
}

COLOR_KEYWORDS = {
    "red":        "primary",
    "brick":      "primary",
    "orange":     "primary",
    "cream":      "secondary",
    "light":      "secondary",
    "white":      "surface",
    "dark":       "dark",
    "black":      "dark",
    "charcoal":   "dark",
    "green":      "accent",
    "teal":       "accent",
    "cyan":       "accent",
    "muted":      "muted",
    "grey":       "muted",
    "gray":       "muted",
    "border":     "border",
    "amber":      "amber",
    "yellow":     "amber",
    "gold":       "amber",
}

SIZE_KEYWORDS = {
    "small":  0.25,
    "tiny":   0.15,
    "little": 0.2,
    "medium": 0.4,
    "large":  0.6,
    "big":    0.65,
    "huge":   0.8,
    "full":   1.0,
    "wide":   None,
    "tall":   None,
}

SIZE_TO_PX = {
    "tiny":   10,
    "small":  14,
    "medium": 20,
    "large":  28,
    "huge":   40,
    "big":    36,
}

POSITION_KEYWORDS = {
    "center":        (0.5,  0.5),
    "middle":        (0.5,  0.5),
    "top":           (0.5,  0.1),
    "bottom":        (0.5,  0.9),
    "left":          (0.1,  0.5),
    "right":         (0.9,  0.5),
    "top-left":      (0.1,  0.1),
    "top-right":     (0.9,  0.1),
    "bottom-left":   (0.1,  0.9),
    "bottom-right":  (0.9,  0.9),
    "upper-center":  (0.5,  0.28),
    "upper":         (0.5,  0.25),
    "lower":         (0.5,  0.75),
}


def _detect_palette(brief: str) -> dict:
    b = brief.lower()
    if any(w in b for w in ["boommates", "boom mates", "brick", "rust belt", "akron"]):
        return PALETTES["boommates"]
    if any(w in b for w in ["greymarket", "grey market", "terminal", "fintech", "dark"]):
        return PALETTES["greymarket"]
    return PALETTES["default"]


def _resolve_color(token: str, palette: dict) -> str:
    role = COLOR_KEYWORDS.get(token.lower())
    if role:
        return palette.get(role, palette["primary"])
    if re.match(r"^#[0-9a-fA-F]{3,6}$", token):
        return token
    return palette["primary"]


def _parse_shape_clause(clause: str, width: int, height: int, palette: dict, index: int) -> dict | None:
    words = clause.lower().split()
    word_set = set(words)

    shape_type = None
    for kw, st in SHAPE_KEYWORDS.items():
        if kw in word_set or kw in clause.lower():
            shape_type = st
            break

    if not shape_type:
        return None

    fill = palette["primary"]
    for kw in COLOR_KEYWORDS:
        if kw in word_set:
            fill = _resolve_color(kw, palette)
            break

    opacity = "1"
    if any(w in word_set for w in ["transparent", "ghost", "faint"]):
        opacity = "0.15"
    elif any(w in word_set for w in ["subtle", "soft", "dim"]):
        opacity = "0.4"
    elif any(w in word_set for w in ["semi", "half"]):
        opacity = "0.6"

    size_frac = 0.3
    for kw, frac in SIZE_KEYWORDS.items():
        if kw in word_set and frac is not None:
            size_frac = frac
            break

    pos_x, pos_y = 0.5, 0.5
    cl = clause.lower()
    # Pass 1: direct token match — catches "top-left" as a single hyphenated word
    matched = next((POSITION_KEYWORDS[w] for w in words if w in POSITION_KEYWORDS), None)
    # Pass 2: bigrams — catches "top left" as two adjacent words
    if matched is None:
        bigrams = [f"{words[i]}-{words[i + 1]}" for i in range(len(words) - 1)]
        matched = next((POSITION_KEYWORDS[b] for b in bigrams if b in POSITION_KEYWORDS), None)
    # Pass 3: longest-first substring — catches embedded positions in longer phrases
    if matched is None:
        for kw in sorted(POSITION_KEYWORDS, key=len, reverse=True):
            if kw in cl:
                matched = POSITION_KEYWORDS[kw]
                break
    if matched:
        pos_x, pos_y = matched

    stroke = "none"
    stroke_width = "0"
    if any(w in word_set for w in ["outline", "stroke", "border", "ring"]):
        stroke = palette["border"]
        stroke_width = "2"

    shape_id = f"{shape_type}-{index + 1}"
    attrs = {"fill": fill, "opacity": opacity}

    if shape_type == "circle":
        r = int(min(width, height) * size_frac / 2)
        cx = int(width * pos_x)
        cy = int(height * pos_y)
        attrs.update({"cx": str(cx), "cy": str(cy), "r": str(r)})

    elif shape_type == "ellipse":
        rx = int(width * size_frac / 2)
        ry = int(height * size_frac / 4)
        if "pill" in word_set or "wide" in word_set:
            rx = int(width * size_frac * 0.8)
            ry = int(height * size_frac * 0.15)
        cx = int(width * pos_x)
        cy = int(height * pos_y)
        attrs.update({"cx": str(cx), "cy": str(cy), "rx": str(rx), "ry": str(ry)})

    elif shape_type == "rect":
        is_bg = any(kw in word_set for kw in ["background", "bg"])
        w = int(width * size_frac)
        h = int(height * size_frac)
        if is_bg:
            x, y, w, h = 0, 0, width, height
        elif any(kw in word_set for kw in ["bar", "strip", "banner", "full", "wide"]):
            w = width
            h = max(int(height * 0.08), 20)
            x = 0
            y = int(height * pos_y - h / 2)
        else:
            x = int(width * pos_x - w / 2)
            y = int(height * pos_y - h / 2)
        rx = "0"
        if any(kw in word_set for kw in ["rounded", "soft", "card", "panel"]):
            rx = str(max(4, int(min(w, h) * 0.08)))
        attrs.update({"x": str(x), "y": str(y), "width": str(w), "height": str(h), "rx": rx})

    elif shape_type == "line":
        x1 = int(width * 0.1)
        x2 = int(width * 0.9)
        y1 = y2 = int(height * pos_y)
        attrs = {
            "x1": str(x1), "y1": str(y1),
            "x2": str(x2), "y2": str(y2),
            "stroke": fill, "stroke-width": "2", "fill": "none"
        }

    elif shape_type == "polygon":
        cx = int(width * pos_x)
        cy = int(height * pos_y)
        s = int(min(width, height) * size_frac / 2)
        if "triangle" in word_set or "arrow" in word_set:
            points = f"{cx},{cy - s} {cx + s},{cy + s} {cx - s},{cy + s}"
        elif "diamond" in word_set:
            points = f"{cx},{cy - s} {cx + s},{cy} {cx},{cy + s} {cx - s},{cy}"
        elif "star" in word_set:
            import math
            pts = []
            for i in range(10):
                angle = math.pi * i / 5 - math.pi / 2
                r = s if i % 2 == 0 else s * 0.45
                pts.append(f"{cx + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}")
            points = " ".join(pts)
        else:
            points = f"{cx},{cy - s} {cx + s},{cy + s} {cx - s},{cy + s}"
        attrs.update({"points": points})

    elif shape_type == "text":
        quoted = re.search(r'"([^"]+)"', clause)
        content = quoted.group(1) if quoted else "text"
        font_size = next((SIZE_TO_PX[kw] for kw in SIZE_TO_PX if kw in word_set), 16)
        is_heading = "heading" in word_set or "title" in word_set
        font_family = "Georgia, 'Times New Roman', serif" if is_heading else "Inter, Arial, sans-serif"
        font_weight = "700" if is_heading else "400"
        x = int(width * pos_x)
        y = int(height * pos_y)
        attrs = {
            "x": str(x),
            "y": str(y),
            "font-size": str(font_size),
            "font-family": font_family,
            "font-weight": font_weight,
            "fill": fill,
            "text-anchor": "middle",
            "dominant-baseline": "middle",
        }
        return {
            "shape": "text",
            "id": shape_id,
            "attrs": attrs,
            "content": content,
            "group": "layer-1",
        }

    elif shape_type == "path":
        cx = int(width * pos_x)
        cy = int(height * pos_y)
        r = int(min(width, height) * size_frac / 2)
        if "wave" in word_set:
            d = (f"M {int(width * 0.05)},{cy} "
                 f"Q {int(width * 0.25)},{cy - r} {int(width * 0.5)},{cy} "
                 f"Q {int(width * 0.75)},{cy + r} {int(width * 0.95)},{cy}")
        elif "arc" in word_set:
            d = f"M {cx - r},{cy} A {r},{r} 0 0,1 {cx + r},{cy}"
        else:
            d = f"M {cx - r},{cy} C {cx},{cy - r} {cx},{cy + r} {cx + r},{cy}"
        attrs.update({"d": d, "fill": "none", "stroke": fill, "stroke-width": "3"})

    if stroke != "none":
        attrs["stroke"] = stroke
        attrs["stroke-width"] = stroke_width

    return {
        "shape": shape_type,
        "id": shape_id,
        "attrs": attrs,
        "group": "layer-1",
    }


def parse_brief(brief: str, width: int, height: int) -> tuple[list[dict], dict]:
    palette = _detect_palette(brief)
    splitters = r",|;|\band\b|\bwith\b|\bplus\b|\bthen\b"
    clauses = [c.strip() for c in re.split(splitters, brief, flags=re.IGNORECASE) if c.strip()]

    descriptors = []
    for i, clause in enumerate(clauses):
        desc = _parse_shape_clause(clause, width, height, palette, i)
        if desc:
            descriptors.append(desc)

    if not descriptors:
        descriptors.append({
            "shape": "rect",
            "id": "rect-1",
            "attrs": {
                "x": str(int(width * 0.1)),
                "y": str(int(height * 0.1)),
                "width": str(int(width * 0.8)),
                "height": str(int(height * 0.8)),
                "fill": palette["secondary"],
                "rx": "8",
                "opacity": "1",
            },
            "group": "layer-1",
        })

    def _z_key(desc: dict) -> int:
        words = set(desc.get("attrs", {}).get("id", "").lower().split("-"))
        clause_words = set()
        # pull from original clause via id index — use shape+id as heuristic
        if desc["shape"] == "text":
            return 2
        # background rects to bottom
        if desc["shape"] == "rect":
            # check if any bg markers ended up in attrs (fill is dark/surface) —
            # simpler: re-check original clause words stored on desc if present
            if desc.get("is_bg"):
                return 0
        return 1

    # tag bg rects during parse so _z_key can see them
    for desc in descriptors:
        if desc["shape"] == "rect" and desc["attrs"].get("x") == "0" and desc["attrs"].get("y") == "0" \
                and desc["attrs"].get("width") == str(width) and desc["attrs"].get("height") == str(height):
            desc["is_bg"] = True

    descriptors.sort(key=_z_key)

    # re-number IDs to match new order
    counters: dict[str, int] = {}
    for desc in descriptors:
        shape = desc["shape"]
        counters[shape] = counters.get(shape, 0) + 1
        desc["id"] = f"{shape}-{counters[shape]}"

    return descriptors, palette


def _make_svg(width: int, height: int) -> etree._Element:
    svg = etree.Element("svg", nsmap=NSMAP)
    svg.set("id", "root")
    svg.set("viewBox", f"0 0 {width} {height}")
    svg.set("width", str(width))
    svg.set("height", str(height))
    return svg


def _add_descriptor(parent: etree._Element, desc: dict) -> etree._Element:
    shape = desc["shape"]
    tag = f"{{{SVG_NS}}}{shape}"
    el = etree.SubElement(parent, tag)
    el.set("id", desc["id"])
    for k, v in desc["attrs"].items():
        el.set(k, str(v))
    if shape == "text":
        el.text = desc.get("content", "text")
    return el


def generate_svg(
    brief: str,
    output_path: str,
    width: int = 800,
    height: int = 600
) -> dict:
    svg = _make_svg(width, height)
    descriptors, palette = parse_brief(brief, width, height)
    groups: dict[str, etree._Element] = {}

    for desc in descriptors:
        group_id = desc.get("group", "layer-1")
        if group_id not in groups:
            g = etree.SubElement(svg, f"{{{SVG_NS}}}g")
            g.set("id", group_id)
            g.set("class", "layer")
            groups[group_id] = g
        _add_descriptor(groups[group_id], desc)

    svg.insert(0, etree.Comment(f" inkscape-mcp | brief: {brief} "))

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
        "palette": palette,
        "shapes": [
            {"id": d["id"], "shape": d["shape"], "group": d.get("group", "layer-1")}
            for d in descriptors
        ],
        "brief": brief,
    }


def add_shape(
    svg_path: str,
    shape: str,
    attrs: dict,
    id: str,
    group: str = None
) -> dict:
    path = Path(svg_path)
    if not path.exists():
        return {"error": f"SVG not found: {svg_path}"}

    tree = etree.parse(str(path))
    root = tree.getroot()

    def find_by_id(element_id: str):
        results = root.findall(f'.//*[@id="{element_id}"]')
        return results[0] if results else None

    if group:
        parent = find_by_id(group)
        if parent is None:
            return {"error": f"Group not found: {group}"}
    else:
        parent = root.find(f"{{{SVG_NS}}}g")
        if parent is None:
            parent = root

    el = etree.SubElement(parent, f"{{{SVG_NS}}}{shape}")
    el.set("id", id)
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
