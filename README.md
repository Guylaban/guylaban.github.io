# Guy Laban — academic website

A fast, dependency-free static site with an **energetic, dynamic, orange-themed
design** and an **automated pipeline that keeps the publication list in sync with
Google Scholar** — automatically attaching the journal/conference logo next to
every paper.

Recreation of <https://www.guylaban.com/>.

## ✨ Features

- **Dynamic hero** with an animated aurora background, pulse accents and
  count-up statistics (citations, h-index, publications, i10-index).
- **Scroll-reveal** sections, a research-interests marquee and spotlight cards.
- **Live publications module** — search, filter (journals / conferences /
  preprints) and sort (newest / most cited), each entry showing its publisher
  logo badge.
- **Automated Google Scholar pipeline** — a weekly GitHub Action pulls new
  publications, assigns the correct venue logo and commits the update.
- Fully responsive, accessible, and respects `prefers-reduced-motion`.

## 🗂 Project structure

```
.
├── index.html                  # the site
├── css/styles.css              # orange theme + animations
├── js/
│   ├── publications.js         # loads data/publications.json, renders + filters
│   └── main.js                 # nav, scroll progress, reveals, counters
├── data/publications.json      # publication data (seed + auto-synced)
├── assets/
│   ├── favicon.svg
│   └── logos/                  # IEEE, ACM, Springer, Frontiers, Nature, arXiv …
├── scripts/
│   ├── fetch_publications.py   # Google Scholar → publications.json
│   └── venue_logos.py          # venue string → logo + publication type
├── .github/workflows/
│   └── update-publications.yml # weekly sync (and manual run)
└── requirements.txt
```

## 🚀 Run locally

It's a static site — just serve the folder:

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## 🔄 The automated publications pipeline

```
Google Scholar  ──►  scripts/fetch_publications.py  ──►  data/publications.json  ──►  website
                         │
                         └─ scripts/venue_logos.py picks the journal/conference logo
```

Run it manually:

```bash
pip install -r requirements.txt
python scripts/fetch_publications.py
```

The script is **non-destructive**: if Google Scholar rate-limits the request it
logs a warning and leaves the existing data untouched (so the pipeline never
wipes the list). Existing papers get their citation counts refreshed; genuinely
new papers are appended and sorted.

### How logos are chosen

`scripts/venue_logos.py` matches keywords in the venue string to a logo badge in
`assets/logos/`. For example *"IEEE Transactions on Affective Computing"* →
`ieee.svg` (journal), *"…ACM Conference on Conversational User Interfaces"* →
`acm.svg` (conference), *"arXiv preprint"* → `arxiv.svg` (preprint). Unknown
venues fall back to a generic document badge. **To support a new publisher**, add
an SVG to `assets/logos/` and a rule to `LOGO_RULES`.

### Scheduling & reliability

The GitHub Action (`.github/workflows/update-publications.yml`) runs every Monday
at 06:00 UTC and can be triggered manually from the **Actions** tab. Google
Scholar blocks data-center IPs, so for reliable CI scraping add a
`SCRAPERAPI_KEY` repository secret — the script will route requests through the
proxy automatically.

## 🌐 Deploy on GitHub Pages

1. Push to GitHub.
2. **Settings → Pages → Build and deployment → Deploy from a branch**, pick the
   branch and `/ (root)` folder.
3. The site is live; the `.nojekyll` file ensures all assets are served as-is.

## 🎨 Customising

- **Colours/animations:** the `:root` variables at the top of `css/styles.css`.
- **Bio / sections:** `index.html`.
- **Publications:** managed automatically, but you can hand-edit
  `data/publications.json` (the pipeline preserves manual URLs).
