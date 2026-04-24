"""Entry point: generate carousel(s) + upload to Notion."""

import argparse
from pathlib import Path

from generator import generate_slides, save_carousel
from notion_uploader import upload_all

OUTPUT_DIR = Path(__file__).parent / "output"


def main():
    parser = argparse.ArgumentParser(description="Carousel Generator + Notion Uploader")
    parser.add_argument("--topic", required=True, help="Carousel topic")
    parser.add_argument("--platform", default="both", choices=["instagram", "linkedin", "both"])
    parser.add_argument("--slides", type=int, default=7)
    parser.add_argument("--skip-notion", action="store_true")
    args = parser.parse_args()

    platforms = ["instagram", "linkedin"] if args.platform == "both" else [args.platform]
    for p in platforms:
        data = generate_slides(args.topic, p, args.slides)
        save_carousel(data)

    if args.skip_notion:
        print("[Main] Skipping Notion upload.")
        return

    print("[Main] Uploading to Notion...")
    urls = upload_all(OUTPUT_DIR)
    print(f"[Main] Uploaded {len(urls)} page(s).")


if __name__ == "__main__":
    main()
