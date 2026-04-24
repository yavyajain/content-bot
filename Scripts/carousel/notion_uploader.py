"""Uploads carousel JSON files to a Notion Content Calendar database.

Required env vars:
  NOTION_API_KEY     — from https://www.notion.so/profile/integrations
  NOTION_DATABASE_ID — your Content Calendar database ID

Expected Notion DB properties (create these before running):
  Name (title), Platform (select), Status (select), Date (date), Slides (number)

Integration must have write access to the database (share → add integration).
"""

import json
import os
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_DB_ID   = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_VERSION = "2022-06-28"
BASE_URL       = "https://api.notion.com/v1"


def _headers() -> dict:
    return {
        "Authorization":  f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type":   "application/json",
    }


def _rich_text(content: str) -> list:
    return [{"type": "text", "text": {"content": (content or "")[:2000]}}]


def _slide_blocks(slides: list[dict]) -> list[dict]:
    blocks = []
    for slide in slides:
        num   = slide.get("number", "?")
        stype = str(slide.get("type", "content")).upper()
        headline = slide.get("headline", "")
        body     = slide.get("body", "")
        visual   = slide.get("visual_direction", "")

        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text(f"Slide {num} ({stype}): {headline}"), "color": "blue"},
        })
        if body:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": _rich_text(body)},
            })
        if visual:
            blocks.append({
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": _rich_text(f"Visual: {visual}"),
                    "icon": {"emoji": "🎨"},
                    "color": "purple_background",
                },
            })
        blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks


def upload_carousel(carousel_path: Path) -> str:
    """Upload a single carousel JSON to Notion. Returns created page URL."""
    if not NOTION_API_KEY or not NOTION_DB_ID:
        raise RuntimeError("NOTION_API_KEY and NOTION_DATABASE_ID must be set")

    data = json.loads(carousel_path.read_text(encoding="utf-8"))

    topic    = data.get("topic", carousel_path.stem)
    platform = str(data.get("platform", "instagram")).capitalize()
    slides   = data.get("slides", [])
    caption  = data.get("caption", "")
    gen_date = (data.get("generated_at") or "")[:10] or date.today().isoformat()

    properties = {
        "Name":     {"title": _rich_text(topic)},
        "Platform": {"select": {"name": platform}},
        "Status":   {"select": {"name": "Draft"}},
        "Date":     {"date":   {"start": gen_date}},
        "Slides":   {"number": len(slides)},
    }

    children = [
        {
            "object": "block", "type": "callout",
            "callout": {
                "rich_text": _rich_text(f"{data.get('brand', {}).get('handle', '@gobi_automates')} | {platform}"),
                "icon": {"emoji": "⚡"},
                "color": "blue_background",
            },
        },
        {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rich_text("Caption")}},
        {"object": "block", "type": "quote",     "quote":     {"rich_text": _rich_text(caption)}},
        {"object": "block", "type": "divider",   "divider":   {}},
        {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rich_text("Slides")}},
        *_slide_blocks(slides),
    ]

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties,
        "children": children[:100],  # Notion limit per request
    }

    resp = requests.post(f"{BASE_URL}/pages", headers=_headers(), json=payload, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Notion API {resp.status_code}: {resp.text}")
    url = resp.json().get("url", "")
    print(f"[Notion] Created: {url}")
    return url


def upload_all(output_dir: Path) -> list[str]:
    """Upload all carousel JSONs that haven't been uploaded. Idempotent via .uploaded.json."""
    log = output_dir / ".uploaded.json"
    done = set(json.loads(log.read_text()) if log.exists() else [])
    urls = []

    for path in sorted(output_dir.glob("*.json")):
        if path.name.startswith(".") or path.stem in done:
            continue
        try:
            urls.append(upload_carousel(path))
            done.add(path.stem)
        except Exception as e:
            print(f"[Notion] FAILED {path.name}: {e}")

    log.write_text(json.dumps(sorted(done), indent=2))
    return urls


if __name__ == "__main__":
    upload_all(OUTPUT_DIR := Path(__file__).parent / "output")
