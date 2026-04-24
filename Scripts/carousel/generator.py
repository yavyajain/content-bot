"""Carousel Generator — branded slide content for @gobi_automates.

Structure: 1 hook + 5 value slides + 1 CTA = 7 slides default.
Run: python generator.py --topic "5 AI tools that save 10hrs/week"
     python generator.py --topic "How RAG works" --platform linkedin
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from brand import BRAND

load_dotenv(Path(__file__).parent / ".env")

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

_SYSTEM = f"""\
You are a viral content strategist for @gobi_automates — an AI automation brand.
You create high-performing carousel posts for Instagram and LinkedIn.

Voice: confident, educational, concise. No fluff. Value-first.
Brand: {BRAND['name']} — {BRAND['tagline']}

Carousel structure:
- Slide 1 (HOOK): Bold statement or question. Max 10 words. Stops the scroll.
- Slides 2 to N-1 (VALUE): One insight per slide. Headline ≤8 words + 2-3 bullets or short paragraph.
- Slide N (CTA): Follow + save + comment prompt.

Return ONLY valid JSON — no markdown fences, no explanation."""

_PROMPT = """\
Create a {slide_count}-slide carousel for {platform} about:
"{topic}"

Return JSON:
{{
  "topic": "{topic}",
  "platform": "{platform}",
  "slides": [
    {{"number": 1, "type": "hook", "headline": "...", "body": "...", "visual_direction": "..."}},
    {{"number": 2, "type": "value", "headline": "...", "body": "...", "visual_direction": "..."}},
    {{"number": {slide_count}, "type": "cta", "headline": "...", "body": "...", "visual_direction": "..."}}
  ],
  "caption": "Full caption with hook + value + [HASHTAGS]",
  "hook_line": "First line of caption (the scroll-stopper)",
  "save_prompt": "Why they should save this post (1 sentence)"
}}"""


def generate_slides(topic: str, platform: str = "instagram", slide_count: int = 7) -> dict:
    print(f"[Carousel] Generating {slide_count}-slide {platform} carousel: {topic}")

    msg = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": _PROMPT.format(
            topic=topic, platform=platform, slide_count=slide_count,
        )}],
    )

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    data = json.loads(raw.strip())

    hashtags = " ".join(BRAND.get(platform, {}).get("hashtags", []))
    if "caption" in data:
        data["caption"] = data["caption"].replace("[HASHTAGS]", hashtags)

    data["brand"] = {
        "handle":    BRAND["handle"],
        "watermark": f"{BRAND['logo_emoji']} {BRAND['handle']}",
        "colors":    BRAND["colors"],
    }
    data["generated_at"] = datetime.now().isoformat()
    return data


def save_carousel(data: dict) -> Path:
    topic    = data.get("topic", "carousel")
    slug     = "".join(c if c.isalnum() else "-" for c in topic.lower())[:50].strip("-")
    date     = datetime.now().strftime("%Y-%m-%d")
    platform = data.get("platform", "instagram")

    path = OUTPUT_DIR / f"{date}-{platform}-{slug}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[Carousel] Saved: {path.name}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--platform", default="instagram", choices=["instagram", "linkedin", "both"])
    parser.add_argument("--slides", type=int, default=7)
    args = parser.parse_args()

    platforms = ["instagram", "linkedin"] if args.platform == "both" else [args.platform]
    for p in platforms:
        data = generate_slides(args.topic, p, args.slides)
        save_carousel(data)


if __name__ == "__main__":
    main()
