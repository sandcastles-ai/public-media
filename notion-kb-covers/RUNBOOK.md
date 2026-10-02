# Runbook: Sandcastles Knowledge Base page covers (Notion)

This document is a complete hand-off for an agent that needs to create, update, or maintain the page-cover images on the **Sandcastles Knowledge Base** Notion database (published at https://help.sandcastles.ai). It covers what exists today, every design rule the owner approved, the platform constraints that were discovered the hard way, the exact tools and repositories required, step-by-step procedures, and the complete source code and data needed to reproduce every published cover byte-for-byte.

The code now lives next to this file in `notion-kb-covers/` (`setup_assets.sh`, `kb_covers.py`, `render.mjs`, `specs.json`), and `specs.json` is the source of truth for every published cover. It was verified on 2026-10-02: running it in a clean directory reproduced all 66 published PNGs byte-identically (Playwright 1.56.1, Chromium build 1194).

---

## 1. What this flow does

1. Each article (a page in the Notion database) gets a **cover image**: a 4000×1000 PNG, rendered from HTML in the Sandcastles app's design system.
2. The image is committed to the public GitHub repo **`sandcastles-ai/public-media`** in the folder **`notion-kb-covers/`**, named after the article title (slugified).
3. The Notion page's cover is set to the image's **raw GitHub URL** (`https://raw.githubusercontent.com/sandcastles-ai/public-media/main/notion-kb-covers/<slug>.png`, with `?v=N` appended when an image has been replaced).
4. The same image serves two very different crops: the **page cover** (a wide, short strip at the top of the article) and the **gallery card** (a roughly 1.4–1.9:1 crop of the middle, if the database is shown as a gallery). The layout is designed so both look intentional.

Current state: **all 66 articles have covers** (one of them, "How to use the Hook Machine in Sandcastles", is currently in the Notion trash; see section 11).

---

## 2. Access, connectors, tools and repositories required

### 2.1 Connectors / MCP tools

| Need | Tool | Used for |
|---|---|---|
| **Notion connector (MCP)**, authenticated to the `sandcastlesai` workspace with edit access to the Knowledge Base | `notion-fetch` | Read an article (content, properties, current `cover`). Pass the page ID (32 hex chars, with or without dashes) as `id`. |
| | `notion-query-data-sources` | List all articles. Use `{"data": {"mode": "rows", "data_source_url": "collection://33aacc48-f1da-8083-a296-000bc2408cdc", "limit": 100}}`. |
| | `notion-update-page` | Set a cover (`command: "update_properties"`, `properties: {}`, `cover: "<url>"`), rename a page (`properties: {"Name": "..."}`), fix article text (`command: "update_content"` with `content_updates` search-and-replace). |
| | `notion-search` / `notion-ai-search` (optional) | Finding pages. Not required if you have IDs. |
| | `notion-create-file-upload`, `notion-create-pages` | **Not needed and do not use for covers.** See section 4.2. |
| **GitHub** with **push access to `sandcastles-ai/public-media`** | `git` CLI (clone/commit/push), or GitHub MCP tools | Hosting the PNGs. |
| GitHub read access to **`harmeetdhingra/sandcastles`** | `git` CLI | Design-system assets, app icon names, Claude plugin command names. |

### 2.2 Repositories

| Repo | Access | Why |
|---|---|---|
| `sandcastles-ai/public-media` (public, default branch `main`) | **Write (push)** | Hosts the covers, this runbook, the scripts and `specs.json` in `notion-kb-covers/`. Covers are referenced by raw URL on `main`, so commits go **directly to `main`** in this repo (the owner approved this; it only holds media). |
| `harmeetdhingra/sandcastles` | Read | `sandcastles-app/public/` holds the logo SVG/PNG and the platform icons used in covers; `sandcastles-app/src/` holds the icon names the covers must match; `sandcastles-app/public/sandcastles-claude-plugin-v*.zip` holds the real Claude plugin slash-command names. **Never push to `main` of this repo**, and do not modify it for this task. |

### 2.3 Runtime

- **Python 3** (standard library only).
- **Node.js 18+** with **Playwright 1.56.1** and its **Chromium build 1194** (`npm i playwright@1.56.1` then `npx playwright install chromium`, unless that Chromium is already provisioned). Other Playwright versions ship other Chromium builds, which can change PNG bytes.
- **curl**.
- Outbound HTTPS to: `unpkg.com`, `cdn.jsdelivr.net`, `rsms.me`, `fonts.gstatic.com` (asset setup), `raw.githubusercontent.com` (verification), `help.sandcastles.ai` (optional live check), `github.com` (git).

---

## 3. Key identifiers

| Thing | Value |
|---|---|
| Notion workspace | `sandcastlesai` |
| Database "Sandcastles Knowledge Base" | https://www.notion.so/sandcastlesai/33aacc48f1da80e8bb80dfcc50925ebc |
| Data source (use in queries) | `collection://33aacc48-f1da-8083-a296-000bc2408cdc` |
| The view the owner works from | `?v=33aacc48f1da80d89c8e000c24b69049` (a List view grouped by Category at time of writing; a Gallery view is planned, which is why covers are designed for gallery cards) |
| Database properties | `Name` (title), `Category` (select), `Tags` (multi-select, only option `Recommended`), `Last Updated` (last edited time) |
| Category options (Notion tag color) | Dashboard (blue), Videos (purple), Ideas (pink), Scripts (green), Projects (red), Exports (gray), Channels (yellow), Persona (blue), Automations (default), Settings (orange), Billing (green), General (brown), Hooks (gray), MCP (brown), API (gray), MCP Workflows (green), Reports (green), Everything Else (gray). Only General, Videos, Ideas, Scripts, Channels, Settings, MCP and Everything Else are currently used. |
| Published help site | https://help.sandcastles.ai; an article is at `https://help.sandcastles.ai/<32-hex page id>` |
| Cover image folder | `sandcastles-ai/public-media` → `notion-kb-covers/` |
| Cover URL pattern | `https://raw.githubusercontent.com/sandcastles-ai/public-media/main/notion-kb-covers/<slug>.png` (+ `?v=N` if the file was ever replaced) |
| Slug rule | lowercase title; `&` → ` and `; remove `'` and `’`; every run of non `[a-z0-9]` → `-`; trim `-` (function `slugify` in the generator) |
| Leftover private page from an abandoned approach | "KB Cover Assets", https://app.notion.com/p/3edacc48f1da817bb53efe7128593746, in the owner's **Private** sidebar section (no teamspace, no database). Unused; safe to delete. |

---

## 4. Platform facts and constraints (learned the hard way)

### 4.1 How Notion displays the image (measured on help.sandcastles.ai)

| Surface | Measured box | Crop behaviour |
|---|---|---|
| Article page cover, desktop | **30vh tall**, full width (1440×270 at a 1440×900 window; 1920×324 at 1920×1080) → roughly 5.3–6:1 | `object-fit: cover`, `object-position: 50% 50%` |
| Article page cover, mobile | 390×253 (≈1.54:1) | Same; only the middle ≈770 of 2000 canvas px are visible |
| Database root page cover | 20vh tall, `object-position: 50% 40%` | Not used by this flow |
| Gallery card image (Notion standard) | Medium cards: 190px tall, card min width 260px; small cards: 124px tall, min 180px | Image is scaled to the card height and cropped to the centre. Typical card ratios are 1.4–1.9:1 → only the middle ≈685–950 of 2000 canvas px are visible, at full height. |

### 4.2 What does NOT work for setting a cover

- The Notion MCP `cover` parameter (on `notion-update-page` and `notion-create-pages`) accepts **only an external https image URL**.
  - `file-upload://<id>` (from `notion-create-file-upload`) → error `Invalid page cover URL.`
  - The bare file-upload ID → same error.
- Uploading the image to Notion, placing it on a page, then setting the cover to its unsigned `prod-files-secure.s3...` URL **appeared to work** (Notion re-attached it) but the cover was **cleared about a minute later**. Do not use this approach.
- The approach that works and has persisted: **public GitHub raw URL** from `sandcastles-ai/public-media`.

### 4.3 Caching

- Notion (and the help site's image proxy) cache external images **per URL**. GitHub's raw CDN also caches per URL for about 5 minutes.
- Therefore: **never rely on overwriting a file at the same URL.** When you replace an image, keep the filename (the naming convention), commit the new bytes, and set the cover to the same URL with a **new** `?v=N` (raw.githubusercontent ignores the query string but every cache treats it as a new URL). Increase N every time the image changes.
- If an article's title changes, rename the file to the new slug with `git mv` and point the cover at the new URL (no `?v` needed for a new path).

### 4.4 Other behaviour

- `notion-fetch` returns `"cover": {"type": "external", "external": {"url": ...}}` when a cover is set, `"cover": null` when there is none.
- Setting a cover does not always change the page's `Last Updated`.
- The published help site can take a few minutes to show a new cover, and the cover image itself loads slowly on first view. A headless check should wait 10–25 seconds before reading `img.naturalWidth`.

---

## 5. Design system and visual rules (all approved by the owner)

The owner's requirements, in their words and as refined in review:

1. Use the **Sandcastles design system**: its colors, fonts, components and logo. Source of truth is `sandcastles-app` (Tailwind config, `src/components/*`, `public/`).
2. When the **title names something specific** (Claude, ChatGPT, Grok, YouTube/TikTok/Instagram, a slash command), **that thing appears in the cover** (its logo, or the exact command).
3. **Optimise for both crops**: the key content sits in the middle so it survives the gallery-card crop; supporting detail fills out the sides of the full-width page cover.
4. **50+ covers must look like one family, but not "a sea of blue"**: consistent structure, with **color varying by category** and enough pop to look good in a grid.
5. **Icons must match the app**: when a cover represents an app feature, use the same icon the app uses for it (section 5.6).
6. Content on covers must be **accurate** to the article and the app (section 6).

### 5.1 Canvas and safe zones

- HTML canvas **2000×500 CSS px**, screenshotted at `deviceScaleFactor: 2` → **4000×1000 PNG** (0.7–1.1 MB each). 4:1 makes the thin desktop page strip relatively taller, so the centre content can be large in gallery cards.
- Visual centre line: **y = 225** (slightly above middle; optical centre).
- **Core (centre) safe zone**: the whole core group must fit within **x 670–1330 (≤ 660 px wide)**. This survives the narrowest gallery crop (1.37:1 → 685 px) and the mobile page crop (≈770 px).
- **Side cards**: 380 px wide at **x 40–420** (left) and **x 1580–1960** (right), vertically centred on y = 225, max height 250, inside the vertical band 90–360. They are visible on the desktop page cover and fully hidden in gallery cards and on mobile.

### 5.2 Background (identical on every cover)

- Base color `#09090b` (Tailwind zinc-950, the app's darkest neutral).
- **Accent glow** (the per-cover color): a blurred radial ellipse, `mix-blend-mode: screen`. Single-accent covers: centred at (1000, 225), radii 640×420, alpha 0.9. Pair covers: two glows, Sandcastles blue at (790, 225) and the partner color at (1210, 225), radii 560×400, alpha 0.85.
- **Dot grid**: 1px white dots at 13% opacity every 24 px, masked away from the centre.
- **Rings**: 7 concentric circles centred on (1000, 225), radii 190–790, white at 12% fading to 3.5%.
- **Vignette** darkening the outer edges.
- **6 glowing nodes** (6 px white dots with an accent halo) sitting on the rings at fixed polar positions.

### 5.3 Core types

| Type | Composition | When |
|---|---|---|
| `pair` | Sandcastles tile → gradient "wire" with end dots and a white pill (e.g. `MCP`, `Plugin`) → partner tile. Width 588 px. | The article is about connecting Sandcastles to another product: MCP setup in Claude / ChatGPT / Grok, updating the Claude plugin. |
| `tile_chip` | One tile + a dark chip with large text. Chip font auto-fits from 56 px down so the chip is ≤ 436 px wide (audit fails below 34 px). Mono font (JetBrains Mono) for slash commands/code, with the leading `/` in the accent color. Optional Sandcastles badge (the app's round blue `logo-icon.png`) on the tile's top-right corner. | Everything else. The chip names what makes the article distinct from its siblings (e.g. "Saved filters", "/channels-recap"). |
| `platforms` | A row of logo tiles (YouTube, TikTok, Instagram, using the app's own PNGs from `sandcastles-app/public/`). | Only the "which platforms are supported" article. |

**Tiles**: 176×176 white rounded squares (radius 44) with a soft accent ring (8 px at 20%), an accent bloom (100 px at 60%) and a drop shadow. Contents: Sandcastles mark (blue `#3b82f6`, the four paths of `logo-banner-dark-mode.svg`), Claude spark (`#d97757`, Simple Icons), OpenAI mark and Grok mark (near-black `#0d0d0d`, LobeHub icons), platform PNGs, or a Heroicons **outline** icon (2.1.5, the same library the app uses via `@heroicons/react`) stroked in the accent color.

### 5.4 Side card components

All side cards share the app's dark-mode card style: background `rgba(24,24,27,0.78)` (zinc-900), 1 px inset white/10 ring, radius 18, padding 22×26, Inter.

| Card type | Renders as |
|---|---|
| `steps` | Uppercase zinc-400 eyebrow (15 px, tracking 0.08em) + 2–3 numbered rows (number in a 28 px accent circle, 19 px text). `→` renders in zinc-500. |
| `list` | Eyebrow + 2–3 rows, each with a 32 px rounded accent-tinted square holding a heroicon. |
| `chips` | Eyebrow + 3–6 small bordered chips (the app's Badge/Code look). |
| `prompt` | Eyebrow (e.g. "Ask Claude") + a chat-bubble with an example request (wraps long URLs). |
| `code` | Mini white tile with a logo or icon + title + optional green "status" badge (the app's green Badge, dark variant) + label + a mono code box with the copy icon (Square2Stack), mirroring the app's MCP settings card. |

### 5.5 Accent colors

| Applies to | Accent |
|---|---|
| General | `#3b82f6` blue-500 (brand) |
| Videos | `#8b5cf6` violet-500 |
| Ideas | `#ec4899` pink-500 |
| Scripts | `#10b981` emerald-500 |
| Channels | `#f59e0b` amber-500 |
| Settings | `#f97316` orange-500 |
| Billing | `#22c55e` green-500 |
| MCP | the partner's brand color: Claude `#d97757`, ChatGPT `#10a37f`, Grok `#a1a1aa` (monochrome). Pair covers use Sandcastles blue on the left glow and the partner color on the right. |
| Everything Else (per page) | Persona `#0ea5e9` sky, Workspaces `#d946ef` fuchsia, Projects `#f43f5e` rose, Reports `#14b8a6` teal, Personal Analytics `#6366f1` indigo, API `#84cc16` lime, Hooks tab `#06b6d4` cyan, Automations `#eab308` yellow |

For a **new category**, pick an unused Tailwind 500 color that echoes its Notion tag color and add it to `CATEGORY_ACCENT`. For a new "Everything Else" article, add its page ID to `PAGE_ACCENT` with an unused color.

### 5.6 Icon consistency with the app (owner rule)

When the tile represents an app feature, use the **app's icon for that feature** (convert the app's PascalCase `@heroicons/react` name to the kebab-case outline file name, e.g. `CloudArrowDown` → `cloud-arrow-down`). Where to look in `harmeetdhingra/sandcastles`:

- Sidebar navigation: `sandcastles-app/src/pages/layout/index.jsx`.
- Buttons: grep the feature's page under `sandcastles-app/src/pages/` for `<Icon icon="...">` next to the button label or tooltip.

Current mapping (decided with the owner):

| Feature / cover | App icon | Cover tile icon |
|---|---|---|
| Videos tab | VideoCamera (sidebar) | `video-camera` |
| Ideas tab | QueueList (sidebar) | `queue-list` |
| Channels tab | Users (sidebar) | `users` |
| Persona tab | Swatch (sidebar) | `swatch` |
| Reports tab | ChartPie (sidebar) | `chart-pie` |
| Hooks tab | Key (sidebar) | `key` |
| Automations tab | Bolt (sidebar) | `bolt` |
| Scripts tab | DocumentText (sidebar) | `document-text` |
| Projects tab | Folder (sidebar) | `folder` |
| Settings | Cog6Tooth (sidebar) | `cog-6-tooth` |
| Export (Videos) and Export ideas | CloudArrowDown (every Export button, and the Exports sidebar item) | `cloud-arrow-down` |
| Bulk analyze | Bolt (Bulk Analyze button, `pages/videos/list/smartRow.jsx`) | `bolt` |
| More Like This | ArrowPathRoundedSquare ("More like this" button, `pages/channels/*`) | `arrow-path-rounded-square` |
| **Exception:** Personal analytics | Home (Dashboard sidebar item) | `presentation-chart-line` (owner chose to keep it) |
| **Exception:** Credits | CreditCard in the app, but CreditCard is already the Compare plans cover's icon | `circle-stack` (owner asked for an icon no other cover uses) |

Avoid reusing one icon for two different concepts. Check the current specs (section 13) before choosing.

---

## 6. Content rules (accuracy)

These apply to every chip and side card:

- Every fact must come from **the article itself**, or from the **app's source** when the article is wrong. Use the app's exact wording for tabs, buttons, filters and plans ("Add video URL", "Outlier Score", "Watchlist").
- Never invent numbers, prices, limits, URLs or features.
- Respect the character limits in the spec schema (section 7). Sentence case, no trailing periods, `→` for navigation paths.
- **Slash commands** must match the Claude plugin. The valid commands (plugin v1.0.6, `sandcastles-app/public/sandcastles-claude-plugin-v1.0.6.zip`, `commands/*.md`) are: `/analytics /analyze /channels-add /channels-recap /channels-search /channels-suggest /formats-global /formats-watchlist /hooks-global /hooks-watchlist /insight /rules /topics /video-suggest /videos-global /videos-watchlist`. If a newer plugin zip exists, re-check against it.
- **Idea detail keyboard shortcuts** (app source `sandcastles-app/src/pages/ideas/detail/index.jsx`): S shortlist, D discard, C create script, A go to analysis, E edit notes, ArrowUp/ArrowDown move between ideas, Esc closes. The **Video detail page** (`src/pages/videos/detail/body/desktopVideo.jsx`) uses A = Add to project and E = Export for LLM, which is correct for that page.
- **Workspace guests are Titan-plan only** (app `src/pages/settings/plans.jsx` lists "Guest access" only under Titan; the API rejects guest invites below Titan).
- If an article's text is wrong or is placeholder content, base the cover on the app and **tell the owner** rather than repeating the error.

---

## 7. Spec format

Each cover is defined by one JSON object in `specs.json` (stored as `notion-kb-covers/specs.json`):

```json
{
  "page_id": "32-hex Notion page id",
  "title": "Exact Notion title (determines the file name)",
  "category": "Notion Category (determines the accent)",
  "core": { ... },
  "left": { ... card ... },
  "right": { ... card ... }
}
```

`core` (pick one):

- `{"type": "pair", "left": "sandcastles", "right": "claude" | "chatgpt" | "grok", "pill": "<=6 chars"}`
- `{"type": "tile_chip", "tile": "<heroicon name> | sandcastles | claude | chatgpt | grok | youtube | tiktok | instagram", "badge": "sandcastles" | null, "chip": "<=18 chars", "mono": true | false}`. For "(Sandcastles MCP in Claude)" articles: `tile: "claude"`, `badge: "sandcastles"`, `chip` = the exact slash command, `mono: true`.
- `{"type": "platforms", "items": ["youtube", "tiktok", "instagram"]}` (only platforms the article names)

Cards (use two different types per cover where possible: left = what/where, right = how or an example):

- `{"type": "steps", "eyebrow": "<=24", "items": ["<=28", "<=28", "<=28"]}` (2–3 items)
- `{"type": "list", "eyebrow": "<=24", "items": [{"icon": "<heroicon>", "text": "<=28"}, ...]}` (2–3 items)
- `{"type": "chips", "eyebrow": "<=24", "items": ["<=16", ...]}` (3–6 items, ≤ 64 characters in total)
- `{"type": "prompt", "eyebrow": "<=24", "text": "<=90"}`
- `{"type": "code", "mark": "sandcastles | claude | chatgpt | grok | <heroicon>", "title": "<=16", "badge": "<=12" | null, "label": "<=22", "code": "<=26"}`

Every heroicon name used anywhere must be in the `HEROICONS` list in `setup_assets.sh` (add new ones there, then re-run the setup).

---

## 8. Procedures

### 8.1 One-time setup

```bash
git clone https://github.com/harmeetdhingra/sandcastles            # read-only use
git clone https://github.com/sandcastles-ai/public-media             # covers live in notion-kb-covers/
mkdir kb-covers && cd kb-covers                                     # work outside both repos
cp ../public-media/notion-kb-covers/{setup_assets.sh,kb_covers.py,render.mjs,specs.json} .
npm i playwright@1.56.1 && npx playwright install chromium          # skip the install step if Chromium build 1194 is provisioned
SANDCASTLES_REPO=../sandcastles bash setup_assets.sh
python3 kb_covers.py              # writes out/<slug>.html + out/manifest.json (optionally: python3 kb_covers.py specs.json <slug-or-page-id> ...)
node render.mjs                   # writes out/<slug>.png and runs the layout audit
```

Sanity check: after a full build, every `out/*.png` should be byte-identical to `public-media/notion-kb-covers/*.png` (`cmp`). If not, an asset or font version changed; investigate before publishing.

### 8.2 Add a cover for a new article

1. **Find the article**: `notion-query-data-sources` (rows mode, the data source above) or the URL the owner gives you. Note `page_id`, `Name`, `Category`.
2. **Read it**: `notion-fetch` with the page ID. Check the article for factual problems (commands, shortcuts, plan limits) against the app source (section 6).
3. **Write the spec** (section 7):
   - Pick the core type. Apply the title rule: a product or platform named in the title must appear in the core.
   - Pick the tile icon per section 5.6 (look up the app icon; don't reuse an icon that means something else on another cover).
   - Make the chip unique within the category.
   - Write two side cards using only facts from the article and app.
4. **Accent**: automatic by category. For "Everything Else" or a new category, add to `PAGE_ACCENT` / `CATEGORY_ACCENT`.
5. **Render**: `python3 kb_covers.py specs.json <page_id>` then `node render.mjs`. The audit must print `all covers passed the layout audit`. Fix the spec (shorter text) if not.
6. **Look at it**: open the PNG; also view it at gallery size (crop the middle ≈ 1.5:1 at 290 px wide) and check that the core reads clearly.
7. **Publish**: copy `out/<slug>.png` and the updated `specs.json` (plus `kb_covers.py` / `setup_assets.sh` if you added an accent or icon) to `public-media/notion-kb-covers/`, `git add`, `git commit`, `git pull --ff-only` if needed, `git push origin main`.
8. **Verify the raw URL**: `curl -sS -o /dev/null -w "%{http_code} %{size_download}" https://raw.githubusercontent.com/sandcastles-ai/public-media/main/notion-kb-covers/<slug>.png` → `200 <same byte size as the local file>`.
9. **Set the cover**:

```json
{
  "page_id": "<page_id>",
  "command": "update_properties",
  "properties": {},
  "cover": "https://raw.githubusercontent.com/sandcastles-ai/public-media/main/notion-kb-covers/<slug>.png",
  "allow_async": false
}
```

10. **Verify in Notion**: `notion-fetch` the page and confirm `cover.external.url` is the URL you set. Optionally load `https://help.sandcastles.ai/<page_id>` in a browser after a few minutes.
11. Confirm the committed `specs.json` contains the new spec so the set stays reproducible.

### 8.3 Change an existing cover (icon, text, color)

1. Edit only what was asked in that article's spec in `specs.json` (owner preference: when asked to change an icon, change only the icon).
2. Re-render just that cover (`python3 kb_covers.py specs.json <page_id>` then `node render.mjs`). The audit must pass.
3. Commit and push the replaced PNG (same filename).
4. Set the cover to the same URL with the **next** `?v=N` (the current suffix is the one in the page's cover URL from `notion-fetch`; section 10 is a snapshot as of 2026-10-02). Verify with `curl "<url>?v=N" | md5sum` against the local file, then `notion-fetch`.

### 8.4 An article's title changes

1. Update `title` in the spec. The slug changes.
2. `git mv notion-kb-covers/<old-slug>.png notion-kb-covers/<new-slug>.png` (re-render if the cover content should change too), commit, push.
3. Set the cover to the new URL (no `?v` needed for a new path).
4. Title changes in Notion: `notion-update-page` with `{"command": "update_properties", "properties": {"Name": "<new title>"}}`.

### 8.5 Fixing article text

Use the smallest exact search-and-replace:

```json
{
  "page_id": "<page_id>",
  "command": "update_content",
  "content_updates": [{"old_str": "<exact text from the fetched markdown>", "new_str": "<replacement>"}],
  "allow_async": false
}
```

`old_str` must match the fetched Notion-flavored markdown exactly (backticks appear escaped as `` \` ``). Use `replace_all_matches: true` only when every occurrence should change. Re-fetch to confirm.

### 8.6 Producing many specs at once

Fan out to parallel sub-agents by category (5 agents covered 65 articles in about 4 minutes). Give each one: the list of `{page_id, title, category}`, this document's sections 5.3, 5.6, 6 and 7, the heroicon list, and these instructions: fetch every article with `notion-fetch`; write one spec per article using only facts from it; make chips unique across the batch; write a JSON array to a file; validate it with a script (valid JSON, every page ID once, every character limit, icons in the list, card types valid, no duplicate chips); do not modify Notion. Then review every spec yourself: print all chips and card texts and read them, and spot-check the articles that agents flag.

### 8.7 Review checklist before publishing

- The layout audit passes for every cover.
- Gallery review: render a sheet of all covers cropped like gallery cards (centre crop, 190 px tall, about 290 px wide), grouped by category. Each card must be identifiable by its tile and chip alone, and categories must read as color groups.
- Read every chip and card text once.
- The title rule holds (named products/platforms/commands appear in the core).
- Icons follow section 5.6, and no icon is reused for a different concept.
- Commands, shortcuts and plan limits match section 6.

---

## 9. History of decisions (context for future changes)

1. First version: a blue (brand) background with a white connector card. The owner liked it, then asked for: (a) the named product's logo in the cover (Claude), (b) a layout that works for gallery cards as well as page covers, (c) family consistency without "a sea of blue". Result: the dark base with per-category accent glow, a 4:1 canvas, a centre core with side cards (section 5).
2. Hosting: Notion-native uploads can't be set as covers through the MCP (section 4.2), so covers live in `sandcastles-ai/public-media`.
3. All 66 covers were generated from per-article specs written by parallel agents that read each article, then reviewed (gallery sheet, a text read-through, an automatic layout audit).
4. Fixes found while doing this (all applied in Notion, see section 11).
5. Icon pass: the owner flagged covers whose icons didn't match the app. Twelve tiles were changed to the app's icons (section 5.6), and those covers' URLs were bumped to `?v=2`.

---

## 10. Current state of every cover

Snapshot as of 2026-10-02. `specs.json` and each page's cover URL in Notion are the current source of truth.

Commits in `sandcastles-ai/public-media` (branch `main`): `8509a44` (first cover), `6f7168e` (65 covers), `1b75765` (renamed /topics and /videos-global, Titan-only guest wording), `36e3046` (8 icon fixes), `6508108` (4 tab icon fixes).

Base URL: `https://raw.githubusercontent.com/sandcastles-ai/public-media/main/notion-kb-covers/` + file + version suffix (the exact value currently set as each page cover).

| # | Category | Title | Page ID | Core | Cover file | Suffix |
|---|---|---|---|---|---|---|
| 1 | General | A quick intro to Sandcastles | `343acc48f1da8135983de76acbb4c97d` | `sandcastles` · Quick intro | `a-quick-intro-to-sandcastles.png` | — |
| 2 | General | How does Sandcastles work? (Quick Demo) | `343acc48f1da81499e72cbbd1ce91cc8` | `play-circle` · Quick demo | `how-does-sandcastles-work-quick-demo.png` | — |
| 3 | General | How to use Sandcastles (In-Depth Walkthrough & 4 Workflows) | `343acc48f1da816aab15f850b29d643d` | `academic-cap` · 4 workflows | `how-to-use-sandcastles-in-depth-walkthrough-and-4-workflows.png` | — |
| 4 | Videos | How to Use the Videos Tab | `343acc48f1da8111b738c0202a697499` | `video-camera` · Videos tab | `how-to-use-the-videos-tab.png` | `?v=2` |
| 5 | Videos | How to use the Video Detail Page in Sandcastles | `343acc48f1da81fc9e50cd5607e5c7c7` | `document-chart-bar` · Video detail page | `how-to-use-the-video-detail-page-in-sandcastles.png` | — |
| 6 | Videos | How do I use the filter settings in the Videos tab? | `343acc48f1da81778f3ce8c8b3f3123e` | `funnel` · Filter settings | `how-do-i-use-the-filter-settings-in-the-videos-tab.png` | — |
| 7 | Videos | How do I create a saved filter in the Videos tab? | `343acc48f1da8124b9f3d2b47530d39a` | `bookmark` · Saved filters | `how-do-i-create-a-saved-filter-in-the-videos-tab.png` | — |
| 8 | Videos | How can I open any video in a new tab? | `343acc48f1da81fdbf9be4e39b6fd07f` | `arrow-top-right-on-square` · Open in new tab | `how-can-i-open-any-video-in-a-new-tab.png` | — |
| 9 | Videos | How do I deep analyze a video in the Videos tab? | `343acc48f1da818c9a34e824260e0d3a` | `sparkles` · Deep analyze | `how-do-i-deep-analyze-a-video-in-the-videos-tab.png` | — |
| 10 | Videos | How do I import an individual video by URL into Sandcastles? | `343acc48f1da816885eac41d173f6b0a` | `link` · Import by URL | `how-do-i-import-an-individual-video-by-url-into-sandcastles.png` | — |
| 11 | Videos | What information can you export from the Videos tab? | `343acc48f1da81128848c37138f74eac` | `cloud-arrow-down` · Export | `what-information-can-you-export-from-the-videos-tab.png` | `?v=2` |
| 12 | Videos | I manually added a channel into Sandcastles, why don't I see all their videos? | `343acc48f1da81b5a1a2fad996dba4e8` | `question-mark-circle` · Missing videos | `i-manually-added-a-channel-into-sandcastles-why-dont-i-see-all-their-videos.png` | — |
| 13 | Videos | How to Use the Global Search Feed in the Videos Tab | `354acc48f1da81f79319dda1cb2ea04c` | `globe-alt` · Global search | `how-to-use-the-global-search-feed-in-the-videos-tab.png` | — |
| 14 | Videos | How to Bulk Analyze Multiple Videos Simultaneously | `354acc48f1da81409dc2d66c5b4e6b36` | `bolt` · Bulk analyze | `how-to-bulk-analyze-multiple-videos-simultaneously.png` | `?v=2` |
| 15 | Ideas | How to Use the Ideas Tab | `343acc48f1da813b96aae9239f4ccf9b` | `queue-list` · Ideas tab | `how-to-use-the-ideas-tab.png` | `?v=2` |
| 16 | Ideas | How can I see more information on an individual idea? | `343acc48f1da8123a2dfd3bebf029275` | `eye` · Detail view | `how-can-i-see-more-information-on-an-individual-idea.png` | — |
| 17 | Ideas | What information can you export from the Ideas tab? | `343acc48f1da81f08457e05ed2692acd` | `cloud-arrow-down` · Export ideas | `what-information-can-you-export-from-the-ideas-tab.png` | `?v=2` |
| 18 | Ideas | What is the difference between the Idea Detail and Video Detail pages? | `343acc48f1da81f889caf500b9df8e2f` | `scale` · Idea vs Video | `what-is-the-difference-between-the-idea-detail-and-video-detail-pages.png` | — |
| 19 | Scripts | How to use the Scripts tab | `343acc48f1da81bebbd1e78d7dd074e9` | `document-text` · Scripts tab | `how-to-use-the-scripts-tab.png` | — |
| 20 | Scripts | How to use the Hook Machine in Sandcastles *(in Notion trash)* | `343acc48f1da819f857ede73881a488d` | `bolt` · Hook Machine | `how-to-use-the-hook-machine-in-sandcastles.png` | — |
| 21 | Scripts | What are the 3 different script paths in Sandcastles? | `343acc48f1da810291d0eed98f0b1b5c` | `square-3-stack-3d` · 3 script paths | `what-are-the-3-different-script-paths-in-sandcastles.png` | — |
| 22 | Scripts | How to remix an existing script in Sandcastles | `343acc48f1da81bcbc03fe5fbb23116b` | `arrow-path` · Remix a script | `how-to-remix-an-existing-script-in-sandcastles.png` | — |
| 23 | Scripts | What is the difference between remixing and writing from scratch in Sandcastles? | `343acc48f1da81e9b04df55027cf0b3d` | `scale` · Remix vs scratch | `what-is-the-difference-between-remixing-and-writing-from-scratch-in-sandcastles.png` | — |
| 24 | Scripts | How can I delete the Sandcastles research and use my own? | `343acc48f1da81fe81cbe7b5e603fb16` | `academic-cap` · Edit research | `how-can-i-delete-the-sandcastles-research-and-use-my-own.png` | — |
| 25 | Scripts | How does Sandcastles choose writing styles in scripts flow? | `343acc48f1da81cc892ede348f5c989f` | `pencil-square` · Writing style | `how-does-sandcastles-choose-writing-styles-in-scripts-flow.png` | — |
| 26 | Scripts | How to determine which hook formats get used in the Sandcastles script flow | `343acc48f1da819f8696c46db14bbfdf` | `star` · Hook formats | `how-to-determine-which-hook-formats-get-used-in-the-sandcastles-script-flow.png` | — |
| 27 | Channels | How to use the Channels tab | `343acc48f1da8120969fd4af4f00f35d` | `users` · Channels tab | `how-to-use-the-channels-tab.png` | `?v=2` |
| 28 | Channels | What are the 4 different channel search modes? | `343acc48f1da8127bd1bfd7888580c67` | `magnifying-glass` · 4 search modes | `what-are-the-4-different-channel-search-modes.png` | — |
| 29 | Channels | Why do I have to build a list of channels to use Sandcastles? | `343acc48f1da819a8554cbbf419391a7` | `funnel` · Why a watchlist | `why-do-i-have-to-build-a-list-of-channels-to-use-sandcastles.png` | — |
| 30 | Channels | Why are certain channels not appearing in Sandcastles search results? | `343acc48f1da81a4b876ddd415e7c36a` | `question-mark-circle` · Missing channels | `why-are-certain-channels-not-appearing-in-sandcastles-search-results.png` | — |
| 31 | Channels | What's the ideal number of channels to have in my Watchlist? | `343acc48f1da8141af56e79c1c832722` | `adjustments-horizontal` · Ideal watchlist | `whats-the-ideal-number-of-channels-to-have-in-my-watchlist.png` | — |
| 32 | Channels | How can I find more channels similar to one I already have? | `343acc48f1da815fb1dac919d3839a6b` | `arrow-path-rounded-square` · More Like This | `how-can-i-find-more-channels-similar-to-one-i-already-have.png` | `?v=2` |
| 33 | Channels | How do I manually import new channels into Sandcastles? | `343acc48f1da811f8574d363c015131e` | `link` · Manual import | `how-do-i-manually-import-new-channels-into-sandcastles.png` | — |
| 34 | Channels | Are there limits to how many channels I can have in my Watchlist? | `343acc48f1da81d0b0abf832192d1c1e` | `rectangle-stack` · Channel limits | `are-there-limits-to-how-many-channels-i-can-have-in-my-watchlist.png` | — |
| 35 | Channels | Which social media platforms can I add channels from in Sandcastles? | `343acc48f1da819dae1fd6c9fb5bfcbf` | platforms: youtube, tiktok, instagram | `which-social-media-platforms-can-i-add-channels-from-in-sandcastles.png` | — |
| 36 | Settings | What settings can I change in Sandcastles? | `343acc48f1da8149a010c2f1ba92a8f7` | `cog-6-tooth` · Settings | `what-settings-can-i-change-in-sandcastles.png` | `?v=2` |
| 37 | Settings | How does the credit system work? | `348acc48f1da80d3b20ce46720a275a6` | `circle-stack` · Credits | `how-does-the-credit-system-work.png` | `?v=2` |
| 38 | Settings | How to verify your social channels in Sandcastles | `3a3acc48f1da815482f6fc5df23d45a3` | `shield-check` · Verify channels | `how-to-verify-your-social-channels-in-sandcastles.png` | — |
| 39 | Settings | What are the differences between the Starter, Pro, Visionary, and Titan Plans? | `3a3acc48f1da8193bdbfc9d0843a6874` | `credit-card` · Compare plans | `what-are-the-differences-between-the-starter-pro-visionary-and-titan-plans.png` | — |
| 40 | MCP | How to Set Up the Sandcastles MCP in Claude | `3ecacc48f1da81a5a369c91a2e3ccedf` | pair: sandcastles ↔ claude (`MCP`) | `how-to-set-up-the-sandcastles-mcp-in-claude.png` | — |
| 41 | MCP | How to Set Up the Sandcastles MCP in ChatGPT | `3b7acc48f1da811e8679e9a2fbc8b698` | pair: sandcastles ↔ chatgpt (`MCP`) | `how-to-set-up-the-sandcastles-mcp-in-chatgpt.png` | — |
| 42 | MCP | How to Set Up the Sandcastles MCP in Grok & GrokBot | `3ecacc48f1da81beaa4dff2c209e58d2` | pair: sandcastles ↔ grok (`MCP`) | `how-to-set-up-the-sandcastles-mcp-in-grok-and-grokbot.png` | — |
| 43 | MCP | How to Update the Sandcastles MCP Plugin in Claude | `362acc48f1da819e9118ede5e339b858` | pair: sandcastles ↔ claude (`Plugin`) | `how-to-update-the-sandcastles-mcp-plugin-in-claude.png` | — |
| 44 | MCP | How to use the /analyze tool (Sandcastles MCP in Claude) | `35eacc48f1da813b89e9d1fb1956bd19` | `claude` + Sandcastles badge · /analyze | `how-to-use-the-analyze-tool-sandcastles-mcp-in-claude.png` | — |
| 45 | MCP | How to use the /channels-add skill (Sandcastles MCP in Claude) | `35eacc48f1da812b9fd5c0e748379950` | `claude` + Sandcastles badge · /channels-add | `how-to-use-the-channels-add-skill-sandcastles-mcp-in-claude.png` | — |
| 46 | MCP | How to use the /channels-recap tool (Sandcastles MCP in Claude) | `35eacc48f1da817298a7d675089fd924` | `claude` + Sandcastles badge · /channels-recap | `how-to-use-the-channels-recap-tool-sandcastles-mcp-in-claude.png` | — |
| 47 | MCP | How to use the /channels-search tool (Sandcastles MCP in Claude) | `35eacc48f1da81c9af9ff10bdd425f4a` | `claude` + Sandcastles badge · /channels-search | `how-to-use-the-channels-search-tool-sandcastles-mcp-in-claude.png` | — |
| 48 | MCP | How to use the /channels-suggest tool (Sandcastles MCP in Claude) | `35eacc48f1da81e786aaea0e03ba3b77` | `claude` + Sandcastles badge · /channels-suggest | `how-to-use-the-channels-suggest-tool-sandcastles-mcp-in-claude.png` | — |
| 49 | MCP | How to use the /formats-global tool (Sandcastles MCP in Claude) | `35eacc48f1da819eae1ad01bdca8379b` | `claude` + Sandcastles badge · /formats-global | `how-to-use-the-formats-global-tool-sandcastles-mcp-in-claude.png` | — |
| 50 | MCP | How to use the /formats-watchlist tool (Sandcastles MCP in Claude) | `35eacc48f1da812da25ac3c0673beab4` | `claude` + Sandcastles badge · /formats-watchlist | `how-to-use-the-formats-watchlist-tool-sandcastles-mcp-in-claude.png` | — |
| 51 | MCP | How to use the /hooks-global tool (Sandcastles MCP in Claude) | `35eacc48f1da81dfba78eec4e64e10d3` | `claude` + Sandcastles badge · /hooks-global | `how-to-use-the-hooks-global-tool-sandcastles-mcp-in-claude.png` | — |
| 52 | MCP | How to use the /hooks-watchlist tool (Sandcastles MCP in Claude) | `35eacc48f1da819ebb41cc72808bfbc1` | `claude` + Sandcastles badge · /hooks-watchlist | `how-to-use-the-hooks-watchlist-tool-sandcastles-mcp-in-claude.png` | — |
| 53 | MCP | How to Use the /rules tool? (Sandcastles MCP in Claude) | `362acc48f1da814091f9c6df22bf6abe` | `claude` + Sandcastles badge · /rules | `how-to-use-the-rules-tool-sandcastles-mcp-in-claude.png` | — |
| 54 | MCP | How to use the /topics tool (Sandcastles MCP in Claude) | `35eacc48f1da8174bad6dacdbb12849d` | `claude` + Sandcastles badge · /topics | `how-to-use-the-topics-tool-sandcastles-mcp-in-claude.png` | — |
| 55 | MCP | How to use the /video-suggest tool (Sandcastles MCP in Claude) | `35eacc48f1da81a0b6dcca60c3abf622` | `claude` + Sandcastles badge · /video-suggest | `how-to-use-the-video-suggest-tool-sandcastles-mcp-in-claude.png` | — |
| 56 | MCP | How to use the /videos-global tool (Sandcastles MCP in Claude) | `35eacc48f1da8156861ae0a3ab36c22b` | `claude` + Sandcastles badge · /videos-global | `how-to-use-the-videos-global-tool-sandcastles-mcp-in-claude.png` | — |
| 57 | MCP | How to Use the /videos-watchlist tool (Sandcastles MCP in Claude) | `35eacc48f1da8184ae51e16da2e98968` | `claude` + Sandcastles badge · /videos-watchlist | `how-to-use-the-videos-watchlist-tool-sandcastles-mcp-in-claude.png` | — |
| 58 | MCP | The Hook Machine Workflow (Sandcastles MCP + Claude) | `365acc48f1da81688136ce1ea5845b06` | `claude` + Sandcastles badge · Hook Machine | `the-hook-machine-workflow-sandcastles-mcp-claude.png` | — |
| 59 | Everything Else | How to Use the Persona Tab | `343acc48f1da81f293fdcded23f5aaae` | `swatch` · Persona tab | `how-to-use-the-persona-tab.png` | `?v=2` |
| 60 | Everything Else | How to use the Workspaces feature | `343acc48f1da8167b46ee18bc4762113` | `squares-2x2` · Workspaces | `how-to-use-the-workspaces-feature.png` | `?v=2` |
| 61 | Everything Else | How to Use the Projects Tab | `343acc48f1da8125aa5fe07461c7936f` | `folder` · Projects tab | `how-to-use-the-projects-tab.png` | — |
| 62 | Everything Else | How to Use the Reports Tab | `3bfacc48f1da817aa758e1630e08bbe5` | `chart-pie` · Reports tab | `how-to-use-the-reports-tab.png` | `?v=2` |
| 63 | Everything Else | How to Use the Personal Analytics Dashboard | `3a3acc48f1da8141a6b7d76aa21c19f3` | `presentation-chart-line` · Personal analytics | `how-to-use-the-personal-analytics-dashboard.png` | — |
| 64 | Everything Else | How to use the Sandcastles API | `35eacc48f1da81b2b297de871e4f1667` | `code-bracket` · Sandcastles API | `how-to-use-the-sandcastles-api.png` | — |
| 65 | Everything Else | How to Use the Hooks Tab in Sandcastles | `354acc48f1da811aa801de0d5f5c8844` | `key` · Hooks tab | `how-to-use-the-hooks-tab-in-sandcastles.png` | `?v=2` |
| 66 | Everything Else | How to Use the Automations Tab | `343acc48f1da81aebafcea7eabf89de2` | `bolt` · Automations tab | `how-to-use-the-automations-tab.png` | `?v=2` |

---

## 11. Knowledge Base content changes made, and open issues

Applied in Notion (all verified by re-fetching):

| Article (page ID) | Change |
|---|---|
| How to use the /topics tool… (`35eacc48f1da8174bad6dacdbb12849d`) | Title `/topic` → `/topics` (body already said /topics). Cover file renamed to the new slug. |
| How to use the /videos-global tool… (`35eacc48f1da8156861ae0a3ab36c22b`) | Title and all 5 body mentions `/video-global` → `/videos-global` (including the example prompt). Cover file renamed. |
| How to Update the Sandcastles MCP Plugin in Claude (`362acc48f1da819e9118ede5e339b858`) | `` `/lee` `` → `` `/rules` `` ("for automation rules"). |
| How to use the /channels-suggest tool… (`35eacc48f1da81e786aaea0e03ba3b77`) | `/video-watchlist` → `/videos-watchlist`. |
| How can I see more information on an individual idea? (`343acc48f1da8123a2dfd3bebf029275`) | Shortlist shortcut `'E' Key` → `'S' Key`. |
| What settings can I change in Sandcastles? (`343acc48f1da8149a010c2f1ba92a8f7`) | Guests line now ends "(Titan plan only)". Cover card says "Add guests (Titan only)". |
| How to use the Workspaces feature (`343acc48f1da8167b46ee18bc4762113`) | "Titan plan or higher" → "Guests are only available on the "Titan" plan. On Titan, you can add guests…". Cover card says "Read-only guests (Titan)". |

Open issues (not changed; ask the owner before acting):

- **"How to use the Hook Machine in Sandcastles"** (`343acc48f1da819f857ede73881a488d`) is **in the Notion trash**. Its body was unrelated placeholder text about game-engine "hooks" (`on_click`, `move`, `rotate`). Its cover was built from the app's real hook step instead ("Generate more hooks"; sort by Saved date, Published date, Views, Channel). If the article is restored or rewritten, re-check the cover against the new text.
- **Idea detail arrow keys**: the same idea-detail article says the left/right arrow keys move between ideas, but the app binds ArrowUp/ArrowDown. Not changed yet.
- **"KB Cover Assets"** private page (section 3) is unused and can be deleted by the owner.

---

## 12. Source code

The scripts are stored next to this runbook in `notion-kb-covers/`: `setup_assets.sh` (downloads fonts and icons, copies app assets), `kb_covers.py` (specs to HTML) and `render.mjs` (HTML to PNG plus the layout audit). Copy them into a work directory outside both repos before running them.

Work directory layout after setup:

```
kb-covers/
  setup_assets.sh      downloads fonts and icons, copies app assets
  kb_covers.py         specs.json -> out/<slug>.html + out/manifest.json
  render.mjs           out/*.html -> out/*.png (4000x1000) + layout audit
  specs.json           section 13
  fonts/               InterVariable.woff2, JetBrainsMono-500.woff2
  icons/               <name>.svg and extracted <name>.d path data
  assets/              youtube.png, tiktok.png, instagram.png, logo-icon.png (from sandcastles-app/public)
  logo_paths.txt       the 4 paths of the Sandcastles mark (from logo-banner-dark-mode.svg)
  out/                 generated HTML, PNGs, manifest.json
```

---

## 13. `specs.json`

Stored next to this runbook as `notion-kb-covers/specs.json` (66 specs on 2026-10-02, ordered by category). Add new specs at the end of their category's group.
