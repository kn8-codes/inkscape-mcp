import re
from pathlib import Path


_SKIP_PATTERN = re.compile(r'^(root|layer-\d+|layer_.*)$')

_ELEMENT_RE = re.compile(r'<(rect|circle|ellipse|text|path|line|polygon|polyline)[^>]*\sid="([^"]+)"')

_ANIM_DEFAULTS = {
    "rect":     'y: 20, opacity: 0, duration: 0.4',
    "circle":   'scale: 0, opacity: 0, duration: 0.5, ease: "back.out(1.7)"',
    "ellipse":  'scale: 0, opacity: 0, duration: 0.5, ease: "back.out(1.7)"',
    "text":     'y: 10, opacity: 0, duration: 0.3',
    "path":     'opacity: 0, duration: 0.6',
    "line":     'opacity: 0, duration: 0.6',
    "polygon":  'opacity: 0, duration: 0.6',
    "polyline": 'opacity: 0, duration: 0.6',
}


def generate_gsap(svg_path: str, output_path: str | None = None) -> dict:
    svg_path = Path(svg_path)
    if not svg_path.exists():
        return {"error": f"SVG not found: {svg_path}"}

    out_path = Path(output_path) if output_path else svg_path.with_suffix(".js")

    svg_text = svg_path.read_text()
    elements = _ELEMENT_RE.findall(svg_text)  # [(tag, id), ...]

    filtered = [(tag, eid) for tag, eid in elements if not _SKIP_PATTERN.match(eid)]

    lines = [
        "// import gsap from 'gsap'",
        "",
        "const tl = gsap.timeline();",
        "",
    ]

    for i, (tag, eid) in enumerate(filtered):
        props = _ANIM_DEFAULTS.get(tag, 'opacity: 0, duration: 0.4')
        position = '"<0.1"' if i > 0 else '"<"'
        lines.append(f'tl.from("#{eid}", {{ {props} }}, {position});')

    lines += [
        "",
        "export default tl;",
        "",
    ]

    js = "\n".join(lines)
    out_path.write_text(js)

    return {
        "output": str(out_path),
        "elements_animated": len(filtered),
        "js": js,
    }
