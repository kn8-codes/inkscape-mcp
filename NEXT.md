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
│   ├── generate.py    # brief parser + svg_from_description
│   ├── transform.py   # move, scale, rotate, boolean ops
│   ├── export.py      # export_png, export_svg_clean
│   ├── batch.py       # batch_export_folder
│   └── gsap.py        # generate_gsap — SVG IDs → GSAP timeline JS
├── requirements.txt
└── NEXT.md
```

## stack
- Python 3.11+
- `mcp` SDK — stdio transport
- `lxml` for SVG manipulation
- `inkscape` CLI via subprocess (`--actions`, `--pipe`)
- Runs on M1 alongside other MCP servers

---

## current tools

| Tool | Description |
|---|---|
| `generate_svg` | Brief → GSAP-ready SVG with named IDs and layer groups |
| `add_shape` | Append a shape to an existing SVG by element ID |
| `transform_element` | Translate, scale, or rotate an element by ID |
| `export_png` | Render SVG → PNG via Inkscape CLI |
| `export_svg_clean` | Strip editor metadata, preserve GSAP-safe IDs |
| `generate_gsap` | Read SVG element IDs → staggered GSAP timeline JS |
| `batch_export_folder` | Export all SVGs in a folder to PNG |

---

## what works

- **Brief parser** — comma-separated natural language clauses → shape descriptors
- **Palette auto-detection** — `boommates`, `greymarket`, `default` detected from brief keywords
- **Shape types** — `rect`, `circle`, `ellipse`, `polygon`, `path`, `text`
- **Position keywords** — single tokens (`upper`, `center`, `top-left`) and bigrams (`top left`)
- **Z-order sorting** — background rects first, shapes next, text always on top
- **Background full-bleed** — `background`/`bg` keyword forces `x=0 y=0 w=width h=height`
- **Text y-positions** — `upper`=25%, `upper-center`=28%, `center`=50%, `lower`=75%
- **GSAP timeline generation** — per-type animation defaults, `0.1s` stagger, `back.out` for circles
- **End-to-end browser demo** — inline SVG + CDN GSAP confirmed working in browser

---

## known bugs / limitations

- **Text clipping** — long heading text has no wrapping; clips at card edges on narrow cards
- **Font loading** — `font-family` is a CSS string token only; no `@font-face` or Google Fonts in SVG/PNG export, so renders fall back to system fonts
- **Inkscape CLI untested** — `export_png` and `boolean_op` have not been exercised against a real Inkscape install on M1; may need `--export-filename` flag form depending on Inkscape version
- **Single layer** — all shapes land in `layer-1`; no way to assign elements to separate layers from a brief
- **Keyword-based parser** — no semantic understanding; complex or ambiguous briefs (e.g. overlapping size + position modifiers) can produce wrong geometry

---

## next priorities

1. **Multi-layer support** — recognize `layer-2`, `layer-3` keywords in brief clauses; render groups in declared order
2. **Text wrapping / max-width** — split long strings into `<tspan>` lines based on card width and font-size estimate
3. **Test `export_png` on M1** — verify Inkscape CLI flags, confirm rasterization output matches SVG viewBox
4. **Repeat element support** — parse `"3 circles evenly spaced top"` → generate N elements with computed positions
5. **Design token import** — accept a `colors_and_type.css` file and pipe its custom properties directly into the active palette

---

## animation-ready SVG contract
Every generated SVG follows these rules so GSAP can drive it immediately:
- Root `<svg>` has `id="root"` and explicit `viewBox`
- Every top-level group: `<g id="layer-{n}" class="layer">`
- Every shape: `id="{type}-{n}"` (e.g. `circle-1`, `path-3`)
- No inline transforms on root — GSAP owns transforms
- Paint order: background rects → shapes → text

## decisions (locked)
- Inkscape over Affinity — Affinity has no scripting API yet
- SVG is the primary output, PNG is secondary
- GSAP compatibility is a hard requirement on all generated SVGs
- stdio transport, M1 only for now

## off the table
- GUI — headless only
- Affinity bridge — revisit when Serif ships scripting API
- Windows support
