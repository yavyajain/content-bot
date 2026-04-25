# Claude Code Scheduled Triggers

If you'd rather run these pipelines as Claude Code remote agents (instead of GitHub Actions), here are the three prompts. Each one is a self-contained instruction set you paste into a scheduled trigger at https://claude.ai/code/scheduled.

## How to create a trigger

1. Open https://claude.ai/code/scheduled → **New trigger**.
2. **Name**: see each section below.
3. **Cron**: see each section.
4. **Repository**: your fork URL, e.g. `https://github.com/<you>/content-bot`.
5. **Model**: `claude-sonnet-4-6` (or latest Sonnet).
6. **Allowed tools**: Bash, Read, Write, Edit, Glob, Grep.
7. **Prompt**: paste the corresponding block below. Replace every `<PASTE_...>` placeholder with your real value.

> All API keys live inside the prompt itself — these are stored in your Claude account, not in the public repo. Rotate keys if you ever share screenshots.

---

## 1. daily-instagram-research

**Cron**: `0 6 * * *` (daily 06:00 UTC)

```
You are a scheduled Claude Code agent. Scrape competitor IG posts from the last 7 days via Apify, pick the top 3 by views, analyze them, and commit results to main.

APIFY_API_KEY=<PASTE_APIFY_API_KEY>

STEPS:
1. Read Scripts/instagram_bot/competitors.json → list of handles.
2. Call Apify actor apify/instagram-scraper via:
   curl -sS -X POST 'https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token='$APIFY_API_KEY -H 'Content-Type: application/json' -d '{"directUrls":["https://www.instagram.com/<handle>/"...],"resultsType":"posts","resultsLimit":30,"addParentData":false}' — combine all handle URLs into one run.
3. Filter to posts from the last 168 hours where videoViewCount or videoPlayCount >= 10000.
4. Pick top 3 by views.
5. For each winner, write (a) why it worked — hook mechanics, pattern interrupts, emotional trigger, visual composition; (b) 5 distinct spin angles tailored for an AI automation audience.
6. Write Scripts/instagram_bot/output/YYYY-MM-DD.json with: generated_at, scrape_window_hours=168, winners=[{handle, url, caption, views, likes, comments, timestamp, why_it_worked, spin_angles:[5]}].
7. Write a Scripts/instagram_bot/output/YYYY-MM-DD.md summary. Vary sentence length, avoid AI-cliché filler.
8. git add Scripts/instagram_bot/output/, commit, push to main.

If <3 qualifying posts, lower threshold to 5000 and retry. Report 1-line summary at end.
```

---

## 2. weekly-linkedin-visuals

**Cron**: `0 8 * * 1` (Mondays 08:00 UTC)

```
You are a scheduled Claude Code agent. Generate an AI-educational diagram, render it as a branded PNG, write a humanized caption, commit to repo, and publish to LinkedIn via a Make.com webhook.

OPENAI_API_KEY=<PASTE_OPENAI_API_KEY>
MAKE_WEBHOOK=<PASTE_MAKE_WEBHOOK_URL>

STEPS:
1. Read Scripts/linkedin_visuals/topics.json ({next_index, topics[]}). Pick topics[next_index]. Update next_index = (next_index + 1) % len(topics). Write back. slug = first 50 chars of topic, lowercased, non-alphanum→dash. today = YYYY-MM-DD UTC. stem = Scripts/linkedin_visuals/output/<today>-<slug>.

2. Design a left-to-right flow: 6–10 nodes, 5–12 edges, labels ≤4 words. Build Excalidraw JSON. Reference Scripts/linkedin_visuals/generator.py for the element schema and layout. Save to <stem>.excalidraw.

3. PNG via OpenAI gpt-image-1:
   curl -sS -X POST https://api.openai.com/v1/images/generations -H 'Authorization: Bearer '$OPENAI_API_KEY -H 'Content-Type: application/json' -d '{"model":"gpt-image-1","size":"1536x1024","n":1,"prompt":"Hand-drawn whiteboard sketch, Excalidraw-style technical diagram of <TOPIC>. Rough pen strokes, sketchnote aesthetic. Dark navy background. Cyan and purple stroke accents. White hand-printed labels in boxes with arrows showing: <node1 → node2 → ...>. Clean and minimal."}'
   Decode b64_json → save <stem>.png.

4. Write a 120–180 word LinkedIn caption. Avoid: em-dashes as connectors, rule-of-three, banned filler (unlock, dive into, leverage, foster, robust, seamless, cutting-edge, revolutionize). Vary sentence length. Include one specific concrete example. Save to <stem>.caption.txt.

5. git add → commit → push to main. image_url = 'https://raw.githubusercontent.com/<your-user>/content-bot/main/Scripts/linkedin_visuals/output/<today>-<slug>.png'. Verify it returns 200 (retry up to 3× with 5s sleep).

6. POST to Make webhook:
   curl -sS -X POST $MAKE_WEBHOOK -H 'Content-Type: application/json' -d '{"text":"<caption>","image_url":"<url>","title":"<topic>","alt_text":"AI diagram: <topic>"}'
   Expect 200 "Accepted".

7. Report: '<TOPIC> → webhook 200' or '<TOPIC> → FAILED <status>: <body>'.
```

---

## 3. biweekly-carousel-notion

**Cron**: `0 9 * * 1,4` (Mondays + Thursdays 09:00 UTC)

```
You are a scheduled Claude Code agent. Generate a 7-slide carousel (IG + LinkedIn variants) from the latest IG research, commit to repo, and upload to Notion.

NOTION_API_KEY=<PASTE_NOTION_API_KEY>
NOTION_DATABASE_ID=<PASTE_NOTION_DATABASE_ID>

STEPS:
1. Find newest JSON in Scripts/instagram_bot/output/. Read it. topic = winners[0].spin_angles[0].
2. Generate two variants (IG + LinkedIn) with the same topic, different voice. Each = 7 slides: hook, 5 value, CTA. Slide schema: {index, type, title, body, visual_cue}.
3. Write Scripts/carousel/output/YYYY-MM-DD-<slug>.json with {generated_at, source_topic, instagram:{slides, caption, hashtags}, linkedin:{slides, caption, hashtags}}.
4. For each platform, POST a Notion page to https://api.notion.com/v1/pages with Authorization: Bearer $NOTION_API_KEY, Notion-Version: 2022-06-28. Body: parent.database_id=$NOTION_DATABASE_ID, properties={Name(title), Platform(select), Status(select=Draft), Date, Slides=7, Hook(rich_text=slide1.title), Source Topic, Caption, Tags(multi_select=[AI,Automation])}, children=[heading_2 + paragraph per slide, divider between].
5. git add → commit → push to main.

Required Notion DB properties: Name (title), Platform (select: Instagram/LinkedIn/Both), Status (select: Draft/Review/Ready/Posted), Date (date), Slides (number), Hook (rich_text), Source Topic (rich_text), Caption (rich_text), Tags (multi_select).

If IG output dir is empty or stale (>7 days), abort. Report topic + 2 Notion page URLs.
```

---

## Tips

- Triggers run in isolated cloud sessions with a fresh git checkout each time. They have no memory between runs — everything they need lives in the prompt or the repo.
- Minimum cron interval is 1 hour.
- Cron is always UTC. Convert your local time before pasting.
- To delete a trigger, go to https://claude.ai/code/scheduled and delete it from the UI.
