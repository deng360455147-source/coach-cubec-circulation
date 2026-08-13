#!/usr/bin/env python3
"""Render the B01 research framework template as a deterministic SVG."""

from __future__ import annotations

import argparse
import html
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


NODE_POSITIONS = {
    "context": (60, 110),
    "question": (390, 110),
    "evidence": (720, 110),
    "model_a": (1050, 55),
    "model_b": (1050, 225),
    "diagnosis": (1050, 500),
    "bottleneck": (650, 500),
    "action": (250, 500),
}

NODE_SIZE = (270, 125)


def wrap_text(value: str, width: int = 16) -> list[str]:
    clean = " ".join(str(value).split())
    if not clean:
        return [""]
    return [clean[i : i + width] for i in range(0, len(clean), width)][:3]


def center(position: tuple[int, int]) -> tuple[int, int]:
    x, y = position
    w, h = NODE_SIZE
    return x + w // 2, y + h // 2


def edge_path(start: str, end: str) -> str:
    sx, sy = center(NODE_POSITIONS[start])
    ex, ey = center(NODE_POSITIONS[end])
    if start in {"model_a", "model_b"} and end == "diagnosis":
        return f"M {sx} {sy + NODE_SIZE[1] // 2} L {sx} {ey - NODE_SIZE[1] // 2}"
    direction = 1 if ex >= sx else -1
    return (
        f"M {sx + direction * NODE_SIZE[0] // 2} {sy} "
        f"L {ex - direction * NODE_SIZE[0] // 2} {ey}"
    )


def render_svg(data: dict) -> str:
    required = set(NODE_POSITIONS)
    nodes = data.get("nodes", {})
    missing = sorted(required - set(nodes))
    if missing:
        raise ValueError(f"missing nodes: {', '.join(missing)}")

    title = html.escape(str(data.get("title", "研究框架")))
    subtitle = html.escape(str(data.get("subtitle", "")))
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="720" viewBox="0 0 1600 720">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#466178"/></marker>',
        '<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0b2239" flood-opacity="0.12"/></filter>',
        "</defs>",
        '<rect width="1600" height="720" fill="#F7F9FC"/>',
        f'<text x="60" y="48" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="30" font-weight="700" fill="#12263A">{title}</text>',
        f'<text x="60" y="78" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="16" fill="#5B6B7B">{subtitle}</text>',
    ]

    edges = [
        ("context", "question"),
        ("question", "evidence"),
        ("evidence", "model_a"),
        ("evidence", "model_b"),
        ("model_a", "diagnosis"),
        ("model_b", "diagnosis"),
        ("diagnosis", "bottleneck"),
        ("bottleneck", "action"),
    ]
    for start, end in edges:
        lines.append(
            f'<path d="{edge_path(start, end)}" fill="none" stroke="#466178" stroke-width="3" marker-end="url(#arrow)"/>'
        )

    fills = {
        "context": "#EAF2FF",
        "question": "#EAF2FF",
        "evidence": "#FFF4D6",
        "model_a": "#E8F5EF",
        "model_b": "#E8F5EF",
        "diagnosis": "#EAF2FF",
        "bottleneck": "#FFF0EB",
        "action": "#EEEAFB",
    }
    for node_id, (x, y) in NODE_POSITIONS.items():
        node = nodes[node_id]
        node_title = html.escape(str(node.get("title", node_id)))
        body_lines = wrap_text(str(node.get("body", "")))
        lines.append(
            f'<rect x="{x}" y="{y}" width="{NODE_SIZE[0]}" height="{NODE_SIZE[1]}" rx="18" fill="{fills[node_id]}" stroke="#B7C5D3" stroke-width="2" filter="url(#shadow)"/>'
        )
        lines.append(
            f'<text x="{x + 20}" y="{y + 36}" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="21" font-weight="700" fill="#17324D">{node_title}</text>'
        )
        for index, body_line in enumerate(body_lines):
            lines.append(
                f'<text x="{x + 20}" y="{y + 68 + index * 23}" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="16" fill="#40566B">{html.escape(body_line)}</text>'
            )

    source_ids = "、".join(str(item) for item in data.get("source_ids", []))
    lines.append(
        f'<text x="60" y="690" font-family="PingFang SC, Microsoft YaHei, sans-serif" font-size="14" fill="#6D7C8B">来源与证据ID：{html.escape(source_ids or "待登记")}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


def self_test() -> int:
    sample = {
        "title": "示例研究框架",
        "subtitle": "仅用于程序自检",
        "nodes": {
            node_id: {"title": node_id, "body": "测试内容"}
            for node_id in NODE_POSITIONS
        },
        "source_ids": ["E001"],
    }
    svg = render_svg(sample)
    with tempfile.NamedTemporaryFile(suffix=".svg") as output:
        output.write(svg.encode("utf-8"))
        output.flush()
        ET.parse(output.name)
    print("PASS: research framework SVG self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", help="research framework JSON")
    parser.add_argument("output", nargs="?", help="output SVG")
    parser.add_argument("--allow-template", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.input or not args.output:
        parser.error("input and output are required unless --self-test is used")

    input_path = Path(args.input)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if data.get("template_mode") and not args.allow_template:
        raise SystemExit("FAIL: replace template placeholders and set template_mode=false")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_svg(data), encoding="utf-8")
    ET.parse(output_path)
    print(f"PASS: wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
