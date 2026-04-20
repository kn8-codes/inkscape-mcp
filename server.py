"""
inkscape-mcp — agent-driven vector graphics via Inkscape CLI
transport: stdio
target: animation-ready SVG for GSAP
"""

import asyncio
import json
import subprocess
import tempfile
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.generate import generate_svg
from tools.transform import transform_element
from tools.export import export_png, export_svg_clean
from tools.batch import batch_export_folder
from tools.gsap import generate_gsap

app = Server("inkscape-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_svg",
            description="Generate animation-ready SVG from a creative brief. Every shape gets a unique ID, every group is named. Output is GSAP-compatible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "brief": {"type": "string", "description": "Creative brief — describe what you want"},
                    "width": {"type": "integer", "default": 800},
                    "height": {"type": "integer", "default": 600},
                    "output_path": {"type": "string", "description": "Where to write the SVG"}
                },
                "required": ["brief", "output_path"]
            }
        ),
        Tool(
            name="add_shape",
            description="Add a shape to an existing SVG file",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_path": {"type": "string"},
                    "shape": {"type": "string", "enum": ["rect", "circle", "ellipse", "polygon", "path"]},
                    "attrs": {"type": "object", "description": "Shape attributes: cx, cy, r, x, y, width, height, d, points, fill, stroke, etc."},
                    "id": {"type": "string", "description": "Element ID — must be unique, used by GSAP"},
                    "group": {"type": "string", "description": "Parent group ID to add shape into"}
                },
                "required": ["svg_path", "shape", "attrs", "id"]
            }
        ),
        Tool(
            name="transform_element",
            description="Move, scale, or rotate an element in an SVG by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_path": {"type": "string"},
                    "element_id": {"type": "string"},
                    "translate": {"type": "array", "items": {"type": "number"}, "description": "[x, y]"},
                    "scale": {"type": "array", "items": {"type": "number"}, "description": "[sx, sy] or [s]"},
                    "rotate": {"type": "number", "description": "degrees"}
                },
                "required": ["svg_path", "element_id"]
            }
        ),
        Tool(
            name="export_png",
            description="Render SVG to PNG at specified resolution",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_path": {"type": "string"},
                    "output_path": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "dpi": {"type": "integer", "default": 96}
                },
                "required": ["svg_path", "output_path"]
            }
        ),
        Tool(
            name="export_svg_clean",
            description="Export a clean, optimized SVG — strips editor metadata, preserves IDs for GSAP",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_path": {"type": "string"},
                    "output_path": {"type": "string"}
                },
                "required": ["svg_path", "output_path"]
            }
        ),
        Tool(
            name="boolean_op",
            description="Boolean operation between two shapes by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_path": {"type": "string"},
                    "id_a": {"type": "string"},
                    "id_b": {"type": "string"},
                    "operation": {"type": "string", "enum": ["union", "difference", "intersection", "exclusion"]},
                    "result_id": {"type": "string", "description": "ID for the resulting shape"}
                },
                "required": ["svg_path", "id_a", "id_b", "operation", "result_id"]
            }
        ),
        Tool(
            name="batch_export_folder",
            description="Export all SVGs in a folder to PNG",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_folder": {"type": "string"},
                    "output_folder": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"}
                },
                "required": ["input_folder", "output_folder"]
            }
        ),
        Tool(
            name="generate_gsap",
            description="Read element IDs from an SVG and generate a matching GSAP animation JS file with per-type defaults and staggered timing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_path": {"type": "string", "description": "Path to the source SVG file"},
                    "output_path": {"type": "string", "description": "Where to write the JS file (defaults to svg_path with .js extension)"}
                },
                "required": ["svg_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "generate_svg":
            result = generate_svg(**arguments)
        elif name == "add_shape":
            from tools.generate import add_shape
            result = add_shape(**arguments)
        elif name == "transform_element":
            result = transform_element(**arguments)
        elif name == "export_png":
            result = export_png(**arguments)
        elif name == "export_svg_clean":
            result = export_svg_clean(**arguments)
        elif name == "boolean_op":
            from tools.transform import boolean_op
            result = boolean_op(**arguments)
        elif name == "batch_export_folder":
            result = batch_export_folder(**arguments)
        elif name == "generate_gsap":
            result = generate_gsap(**arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
