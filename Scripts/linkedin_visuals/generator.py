"""LinkedIn Visual Generator — Excalidraw diagrams for AI/tech topics.

Claude designs a diagram spec (nodes + edges), Python builds valid Excalidraw JSON.
Import the .excalidraw file directly into excalidraw.com.

Run: python generator.py                          # auto-rotate 2 topics
     python generator.py --topic "RAG" --count 1  # custom topic
"""

import argparse
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

TOPICS_FILE = Path(__file__).parent / "topics.json"
OUTPUT_DIR  = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# gobi_automates brand palette
_C = {
    "bg":            "#0A0E27",
    "blue_fill":     "#1E3A5F",
    "purple_fill":   "#2D1B69",
    "teal_fill":     "#0D3D3D",
    "green_fill":    "#0D3322",
    "blue_stroke":   "#00D4FF",
    "purple_stroke": "#8B5CF6",
    "green_stroke":  "#00FF88",
    "white":         "#FFFFFF",
    "muted":         "#94A3B8",
    "arrow":         "#00D4FF",
}

_SCHEMES = {
    "blue":   (_C["blue_fill"],   _C["blue_stroke"]),
    "purple": (_C["purple_fill"], _C["purple_stroke"]),
    "teal":   (_C["teal_fill"],   _C["blue_stroke"]),
    "green":  (_C["green_fill"],  _C["green_stroke"]),
}

_SYSTEM = """\
You are a visual diagram architect for art and design education content on LinkedIn.
Design clear, minimal diagrams explaining art, design, architecture, and creative career concepts in 6-10 components.

Return ONLY a JSON object (no markdown fences, no explanation):
{
  "title": "short diagram title",
  "description": "one-line LinkedIn caption starter",
  "nodes": [
    {"id": "n1", "label": "Component", "sublabel": "optional detail", "color": "blue|purple|teal|green"}
  ],
  "edges": [
    {"from": "n1", "to": "n2", "label": "action"}
  ]
}
Rules: labels ≤4 words, 6-10 nodes, 5-12 edges, left-to-right flow."""

_PROMPT = "Design a diagram explaining: {topic}\n\nFor @artiste360 LinkedIn audience — an art and design school in Mumbai, India that helps students get into top global colleges like RISD, Parsons, UAL, Pratt, and Cambridge."


def _uid() -> str:
    return hex(random.randint(0, 0xFFFFFFFFFFFF))[2:].zfill(12)


def _seed() -> int:
    return random.randint(100000, 999999)


def _ask_claude(topic: str) -> dict:
    msg = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": _PROMPT.format(topic=topic)}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw.strip())


def _layout(nodes: list[dict], edges: list[dict]) -> dict[str, tuple]:
    """Layered left-to-right layout via Kahn's topological sort."""
    ids = [n["id"] for n in nodes]
    adj    = {nid: [] for nid in ids}
    in_deg = {nid: 0  for nid in ids}

    for e in edges:
        src, dst = e.get("from"), e.get("to")
        if src in adj and dst in in_deg:
            adj[src].append(dst)
            in_deg[dst] += 1

    layers: list[list[str]] = []
    queue   = [nid for nid in ids if in_deg[nid] == 0]
    visited: set[str] = set()

    while queue:
        layer, nxt = [], []
        for nid in queue:
            if nid not in visited:
                visited.add(nid)
                layer.append(nid)
                for child in adj[nid]:
                    in_deg[child] -= 1
                    if in_deg[child] == 0:
                        nxt.append(child)
        if layer:
            layers.append(layer)
        queue = nxt

    for nid in ids:
        if nid not in visited:
            layers.append([nid])

    W, H, H_GAP, V_GAP = 220, 90, 140, 60
    max_rows = max(len(l) for l in layers)
    canvas_h = max_rows * (H + V_GAP)
    positions: dict = {}

    for col, layer in enumerate(layers):
        x = col * (W + H_GAP) + 80
        total_h = len(layer) * (H + V_GAP) - V_GAP
        start_y = (canvas_h - total_h) // 2 + 80
        for row, nid in enumerate(layer):
            positions[nid] = (x, start_y + row * (H + V_GAP), W, H)

    return positions


def _rect_and_text(nid: str, x: int, y: int, w: int, h: int, node: dict) -> tuple:
    bg, stroke = _SCHEMES.get(node.get("color", "blue"), _SCHEMES["blue"])
    rid, tid = f"rect_{nid}", f"txt_{nid}"
    ts = int(time.time() * 1000)
    label    = node.get("label", nid)
    sublabel = node.get("sublabel", "")
    text     = f"{label}\n{sublabel}" if sublabel else label
    fs       = 14 if sublabel else 16

    rect = {
        "id": rid, "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 3},
        "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": [{"id": tid, "type": "text"}],
        "updated": ts, "link": None, "locked": False,
    }
    txt = {
        "id": tid, "type": "text",
        "x": x + 8, "y": y + h // 2 - (20 if sublabel else 10),
        "width": w - 16, "height": 40 if sublabel else 20, "angle": 0,
        "strokeColor": _C["white"], "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": None,
        "updated": ts, "link": None, "locked": False,
        "text": text, "fontSize": fs, "fontFamily": 1,
        "textAlign": "center", "verticalAlign": "middle", "baseline": fs - 2,
        "containerId": rid, "originalText": text, "lineHeight": 1.25,
    }
    return rect, txt


def _arrow(edge: dict, positions: dict) -> dict | None:
    src, dst = edge.get("from"), edge.get("to")
    if src not in positions or dst not in positions:
        return None
    sx, sy, sw, sh = positions[src]
    dx, dy, dw, dh = positions[dst]
    ts = int(time.time() * 1000)
    ex, ey = dx - (sx + sw), dy + dh // 2 - (sy + sh // 2)
    return {
        "id": _uid(), "type": "arrow",
        "x": sx + sw, "y": sy + sh // 2,
        "width": ex, "height": ey, "angle": 0,
        "strokeColor": _C["arrow"], "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 2},
        "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": None,
        "updated": ts, "link": None, "locked": False,
        "points": [[0, 0], [ex, ey]],
        "lastCommittedPoint": None,
        "startBinding": {"elementId": f"rect_{src}", "focus": 0, "gap": 4},
        "endBinding":   {"elementId": f"rect_{dst}", "focus": 0, "gap": 4},
        "startArrowhead": None, "endArrowhead": "arrow",
    }


def _title_el(title: str, canvas_w: int) -> dict:
    ts = int(time.time() * 1000)
    return {
        "id": _uid(), "type": "text",
        "x": 40, "y": 20, "width": canvas_w - 80, "height": 50, "angle": 0,
        "strokeColor": _C["blue_stroke"], "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": None,
        "updated": ts, "link": None, "locked": False,
        "text": title, "fontSize": 24, "fontFamily": 1,
        "textAlign": "center", "verticalAlign": "top", "baseline": 22,
        "containerId": None, "originalText": title, "lineHeight": 1.25,
    }


def _watermark_el() -> dict:
    ts = int(time.time() * 1000)
    return {
        "id": _uid(), "type": "text",
        "x": 40, "y": 10, "width": 200, "height": 20, "angle": 0,
        "strokeColor": _C["muted"], "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 0, "opacity": 70,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(), "version": 1, "versionNonce": _seed(),
        "isDeleted": False, "boundElements": None,
        "updated": ts, "link": None, "locked": False,
      "text": "@artiste360",
        "fontSize": 12, "fontFamily": 1,
        "textAlign": "left", "verticalAlign": "top", "baseline": 10,
        "containerId": None, "originalText": "@artiste360",
        "lineHeight": 1.25,
    }


def build_excalidraw(spec: dict) -> dict:
    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    positions = _layout(nodes, edges)

    max_x = max((x + w for x, _, w, _ in positions.values()), default=800)
    elements = [_title_el(spec.get("title", "AI Diagram"), max_x + 80), _watermark_el()]

    for node in nodes:
        if node["id"] in positions:
            x, y, w, h = positions[node["id"]]
            rect, txt = _rect_and_text(node["id"], x, y, w, h, node)
            elements += [rect, txt]

    for edge in edges:
        a = _arrow(edge, positions)
        if a:
            elements.append(a)

    return {
        "type": "excalidraw", "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": _C["bg"]},
        "files": {},
    }


def _next_topics(n: int) -> list[str]:
    data   = json.loads(TOPICS_FILE.read_text())
    topics = data["topics"]
    idx    = data.get("next_index", 0)
    picked = [topics[(idx + i) % len(topics)] for i in range(n)]
    data["next_index"] = (idx + n) % len(topics)
    TOPICS_FILE.write_text(json.dumps(data, indent=2))
    return picked


def generate(topic: str) -> Path:
    print(f"[LinkedIn Visuals] Generating: {topic}")
    spec    = _ask_claude(topic)
    diagram = build_excalidraw(spec)

    slug = "".join(c if c.isalnum() else "-" for c in topic.lower())[:50].strip("-")
    date = datetime.now().strftime("%Y-%m-%d")
    out  = OUTPUT_DIR / f"{date}-{slug}.excalidraw"
    out.write_text(json.dumps(diagram, indent=2))

    cap = OUTPUT_DIR / f"{date}-{slug}.caption.txt"
    cap.write_text(
        f"{spec.get('description', topic)}\n\n"
        "🎨 Follow @artiste360 for art & design education, portfolio tips, and college application guidance.\n"
        "#ArtEducation #DesignSchool #PortfolioTips #ArtCollege #CreativeCareers #RISD #Parsons #UAL #MumbaiArt #Artiste360"
    )
    print(f"[LinkedIn Visuals] Saved: {out.name}")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="Single topic to generate")
    parser.add_argument("--count", type=int, default=2, help="Auto-rotate N topics (default 2)")
    args = parser.parse_args()

    topics = [args.topic] if args.topic else _next_topics(args.count)
    for t in topics:
        generate(t)
    print("[LinkedIn Visuals] Done.")


if __name__ == "__main__":
    main()
