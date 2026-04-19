# inkscape-mcp

Agent-driven vector graphics generation via Inkscape CLI.
Output target: animation-ready SVG for GSAP.

## the pitch
Agent gets a creative brief → generates structured SVG → GSAP animates it.
Every shape gets a meaningful ID. Every group is addressable. No cleanup needed.

## structure
```
inkscape-mcp/
├── server.py          # MCP server — stdio transport
├── tools/
│   ├── generate.py    # svg_from_description (core tool)
│   ├── transform.py   # move, scale, rotate, boolean ops
│   ├── export.py      # export_png, export_pdf, export_svg
│   └── batch.py       # batch_export_folder
├── templates/
│   └── animation_base.svg   # base SVG with GSAP-friendly structure
├── requirements.txt
└── README.md
```

## stack
- Python 3.11+
- `mcp` SDK (same pattern as openclaw-mcp)
- `lxml` for SVG manipulation
- `inkscape` CLI via subprocess (`--actions`, `--pipe`)
- stdio transport — runs on M1 alongside ae-mcp

## tools (MVP)
- `generate_svg` — brief → structured SVG with named groups/IDs
- `add_shape` — rect, circle, ellipse, path, polygon
- `set_fill` / `set_stroke` — color, opacity, stroke-width
- `add_text` — text layer with font control
- `transform` — move, scale, rotate on any element by ID
- `boolean_op` — union, difference, intersection
- `export_png` — render to PNG at any resolution
- `export_svg` — clean SVG output, GSAP-ready

## animation-ready SVG contract
Every generated SVG follows these rules so GSAP can drive it immediately:
- Root `<svg>` has `id="root"` and explicit `viewBox`
- Every top-level group: `<g id="layer-{n}" class="layer">`
- Every shape: `id="{type}-{n}"` (e.g. `circle-1`, `path-3`)
- No inline transforms on root — GSAP owns transforms
- Groups use `transform-origin: center center`

## next
- [ ] Scaffold server.py with mcp SDK (copy openclaw-mcp pattern)
- [ ] Wire `generate_svg` tool — takes brief string, returns SVG path
- [ ] Lock ID naming convention
- [ ] First GSAP test: agent generates → browser animates
- [ ] `batch_export_folder` for asset pipeline use

## decisions (locked)
- Inkscape over Affinity — Affinity has no scripting API yet
- SVG is the primary output, PNG is secondary
- GSAP compatibility is a hard requirement on all generated SVGs
- stdio transport, M1 only for now

## timeline (honest)
- Day 1: server scaffolded, generate_svg working, clean SVG out
- Day 2: ID conventions locked, GSAP test passing
- Day 3: first full brief-to-animation pipeline end-to-end

## off the table
- GUI — headless only
- Affinity bridge — revisit when Serif ships scripting API
- Windows support
