# My Content Manager

Three autonomous AI content pipelines you can clone and run for free.

1. **Daily Instagram research** — scrapes top-performing competitor posts from the last 7 days, picks the winners, and writes 5 spin-angle ideas you can riff on.
2. **Weekly LinkedIn visual** — generates an AI-educational diagram, renders it as a branded PNG, writes a humanized caption, and auto-publishes to LinkedIn.
3. **Biweekly carousel + Notion** — turns the top Instagram spin idea into a 7-slide carousel for both IG and LinkedIn, and uploads it to a Notion content calendar.

All three commit their output back to the repo so you have a permanent record. Designed to run on a schedule with zero manual intervention.

## Two ways to run it

You can deploy this on **GitHub Actions** (free, runs on GitHub's servers) or as **Claude Code scheduled triggers** (free during preview, runs in Anthropic's cloud with Claude as the brain). Both are documented below.

## Setup (5 minutes)

### 1. Fork and clone

```bash
gh repo fork govindgoel2001/content-bot --clone
cd content-bot
```

### 2. Get your API keys

Copy `.env.example` to `.env` (for local runs) and fill in the values:

```bash
cp .env.example .env
```

| Variable | Where to get it | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys | Instagram, LinkedIn, Carousel (if running Python locally) |
| `APIFY_API_KEY` | apify.com → Settings → Integrations | Instagram research |
| `OPENAI_API_KEY` | platform.openai.com → API Keys | LinkedIn visuals (gpt-image-1 PNG render) |
| `NOTION_API_KEY` | notion.so/my-integrations → New integration | Carousel uploader |
| `NOTION_DATABASE_ID` | open your Notion DB, copy the 32-char ID from the URL | Carousel uploader |
| `MAKE_WEBHOOK_URL` | make.com → scenario → Webhooks module → copy URL | LinkedIn auto-publish |

### 3. Pick your runtime

#### Option A: GitHub Actions (recommended for most users)

Already wired up. Just add your keys as repo secrets:

```bash
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..."
gh secret set APIFY_API_KEY --body "apify_api_..."
gh secret set OPENAI_API_KEY --body "sk-proj-..."
gh secret set NOTION_API_KEY --body "ntn_..."
gh secret set NOTION_DATABASE_ID --body "..."
gh secret set MAKE_WEBHOOK_URL --body "https://hook.eu1.make.com/..."
```

Then enable Actions on your fork (Settings → Actions → Allow all). Workflows in `.github/workflows/` run on the schedules baked in:
- `daily-content-bot.yml` → 06:00 UTC daily
- `linkedin-visuals.yml` → 08:00 UTC Mondays
- `carousel-notion.yml` → manual dispatch

#### Option B: Claude Code scheduled triggers

If you have Claude Code installed, see [docs/CLAUDE_TRIGGERS.md](docs/CLAUDE_TRIGGERS.md) for three copy-paste prompts that recreate the full pipeline as remote agents in Anthropic's cloud. No GH Actions runner minutes used.

### 4. Customize

- **Competitors**: edit `Scripts/instagram_bot/competitors.json` with the IG handles you want to track.
- **Topics**: edit `Scripts/linkedin_visuals/topics.json` with the AI/tech topics you want diagrams of.
- **Brand**: change colors and watermark in `Scripts/carousel/brand.py` and `Scripts/linkedin_visuals/generator.py`.
- **Notion DB schema**: see `Scripts/carousel/notion_uploader.py` for the expected properties (Name, Platform, Status, Date, Slides, Hook, Source Topic, Caption, Tags). Match these in your DB or edit the uploader.

### 5. LinkedIn auto-publish (optional, for the visuals pipeline)

The LinkedIn API requires OAuth, which is a hassle. The easiest free workaround:

1. Sign up at [make.com](https://make.com) (free 1000 ops/month).
2. New scenario → **Webhooks → Custom webhook** → copy URL.
3. Add a **LinkedIn → Create an Image Post** module → connect your LinkedIn (one-click OAuth in Make's UI) → map fields:
   - Choose Upload Method: **Link**
   - Image URL: `{{1.image_url}}`
   - Content: `{{1.text}}`
   - Visibility: Anyone
4. Toggle scenario ON, paste the webhook URL into `MAKE_WEBHOOK_URL`.

Done. The agent commits the PNG to your repo, posts the raw GitHub URL + caption to your webhook, and Make publishes to LinkedIn.

## Architecture

```
content-bot/
├── .github/workflows/    # GH Actions schedules
├── Scripts/
│   ├── instagram_bot/    # Apify scrape → Claude analyze → Excel CRM
│   ├── linkedin_visuals/ # Claude designs → Excalidraw JSON + PNG
│   └── carousel/         # 7-slide carousel + Notion upload
└── docs/
    └── CLAUDE_TRIGGERS.md  # Claude Code remote trigger prompts
```

Built with Claude as the writing/analysis brain. Originally for [@gobi_automates](https://instagram.com/gobi_automates).

## License

MIT. Use it, fork it, sell it, whatever. Credit appreciated, not required.
