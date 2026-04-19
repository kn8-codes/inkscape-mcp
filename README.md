# inkscape-mcp

Agent-driven vector graphics generation. Brief in → animation-ready SVG out.

Built for GSAP. Every shape has an ID. Every group is named. No cleanup needed.

## install

```bash
cd inkscape-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Inkscape CLI required
brew install inkscape
```

## run

```bash
python server.py
```

## register in .claude.json

```json
{
  "mcpServers": {
    "inkscape": {
      "command": "/path/to/inkscape-mcp/venv/bin/python",
      "args": ["/path/to/inkscape-mcp/server.py"]
    }
  }
}
```

## the contract

Every SVG this server generates follows these rules so GSAP works immediately:

- Root `<svg id="root">` with explicit `viewBox`
- Top-level groups: `<g id="layer-{n}" class="layer">`
- Every shape: `id="{type}-{n}"` e.g. `circle-1`, `path-3`
- No inline transforms on root element
- Groups use CSS `transform-origin: center center`

## example GSAP usage

```javascript
// After agent generates the SVG and it's in the DOM:
gsap.to("#circle-1", { rotation: 360, duration: 2, repeat: -1 })
gsap.from(".layer", { opacity: 0, stagger: 0.2 })
```

## part of the M1 creative MCP stack

- `inkscape-mcp` — vector / SVG (this repo) — **start here**
- `pixelmator-mcp` — raster / photo editing
- `after-effects-mcp` — motion graphics / compositing
