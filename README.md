# WordPress Community Events Dashboard

A management view of the WordPress community events program: meetups, WordCamps, and the WordCamp application pipeline. Built for DotOrg / Comet + Orion.

**This is deliberately *not* a copy of [events.wordpress.org](https://events.wordpress.org).** That site is the public directory of what's on. This dashboard shows the three things a public listing structurally cannot: the **application pipeline** (what's in flight and where it's stuck), the **decay** (dormant groups, the US-at-zero), and the **trend/synthesis** (2018→2026 trajectory, bench renewal).

> 🌐 **Published publicly** via GitHub Pages at **https://wordpress.github.io/wp-events-dashboard/**. The dashboard data in this repo has been cleared for public release. Note that live API credentials (`api/meetup_secrets.json`, `api/wccentral_secrets.json`) remain git-ignored and must never be committed.

---

## Setup

### 0. Just want to look at it?

No setup needed. The dashboard is one self-contained file:

```
open events-dashboard.html
```

It opens in any browser, works offline, and already contains a data snapshot. Everything below is only for **refreshing** that data.

### 1. Prerequisites

- **Python 3.9+** (the pull scripts and `build_dashboard.py` use only the standard library, nothing to `pip install`).
- To refresh the meetup feed: a **Meetup Pro API credential** (JWT) for the official WordPress chapter.
- To refresh the events/pipeline feed: a **WordCamp Central account** with (a) an Application Password and (b) the ability to log in to central.wordcamp.org in a browser.

### 2. Clone

```
git clone git@github.com:WordPress/wp-events-dashboard.git
cd wp-events-dashboard
```

### 3. Add your credentials (git-ignored, never committed)

```
cp api/meetup_secrets.example.json      api/meetup_secrets.json
cp api/wccentral_secrets.example.json   api/wccentral_secrets.json
```

Then edit each:

- `api/meetup_secrets.json` — fill in the Meetup JWT fields (see `api/API_SETUP.md`).
- `api/wccentral_secrets.json` — your central.wordcamp.org username and an **Application Password** (generate at central.wordcamp.org → your Profile → Application Passwords).

### 4. Pull the feeds

```
python3 api/pull_meetup.py     # -> data.js + history.json   (needs meetup_secrets.json)
python3 api/pull_events.py     # -> event counts             (no auth)
python3 api/pull_pipeline.py   # -> pipeline.json + funnel counts (needs wccentral_secrets.json)
```

### 5. The one manual step: pipeline detail + momentum

The active-funnel **record detail** (which specific ~100 events are in flight) and the `wordcamp-status` **momentum** log are permission-stripped from the Application Password REST. They must be pulled from a **logged-in Central browser session**: an in-page `fetch` with the session cookie + `X-WP-Nonce` against `/wp-json/wp/v2/wordcamps?status=<slug>&context=edit`, or the `wp-admin/index.php?page=wordcamp-reports` pages. Do this weekly at most. (This is the piece most worth turning into a small helper next.)

### 6. Build the dashboard

```
python3 build_dashboard.py
```

Reads `dashboard_data.json` and writes:
- `events-dashboard.html` — standalone, double-click to open
- `events-dashboard.artifact.html` — body-only, for publishing as a Claude Artifact

### 7. Publish (GitHub Pages)

The dashboard is served publicly at **https://wordpress.github.io/wp-events-dashboard/**. Pages serves `index.html` from the repo root, which is a copy of the latest `events-dashboard.html`. After rebuilding, refresh the published copy:

```
cp events-dashboard.html index.html
git add index.html && git commit -m "Update published dashboard" && git push
```

In the repo, **Settings → Pages → Build and deployment → Deploy from a branch → `main` / root** enables hosting.

---

## How the data is wired

`dashboard_data.json` is the single input `build_dashboard.py` renders. It is assembled from the three feeds above plus a couple of baked-in pieces (the SVG map land outline, the bench-renewal numbers from WordCamp Central's Counts report). **Honest state of things:** the per-feed pulls are scripted, but reassembling `dashboard_data.json` from them is currently done by hand. The version in the repo is a working frozen snapshot, so `build_dashboard.py` runs out of the box. Writing one `assemble.py` that merges the feeds into `dashboard_data.json` is the top open task for whoever adopts this.

## The four tabs

- **Overview** — definitions + headline numbers across all three domains.
- **Pipeline** — the WordCamp application funnel (~100 events in flight), where each is stuck, monthly momentum, and the outreach list. The unique value.
- **Meetups** — 704 groups on a world map by activity, the recency curve, and the biggest groups that went quiet (reactivation targets).
- **Events & WordCamps** — bench renewal, the events map, by-year / by-country / by-format. Delegates "what's on" to events.wordpress.org.

## Design notes

- Palette follows [wordpress.org](https://wordpress.org/): WordPress blue `#3858E9` on a light white-gray ground (`#F6F7F7`), white cards, near-black ink (`#1E1E1E`), hairline borders (`#DCDCDE`), serif display.
- Maps are **self-contained inline SVG** (equirectangular projection, land outline baked in), not Leaflet — a published Claude Artifact blocks external tiles, CDN scripts, and web fonts.
- Light theme is forced via CSS custom-property tokens (`data-theme="light"` on `<html>`); the dashboard does not follow system dark mode.

## Lesson worth keeping

For a point-in-time report (like a midpoint post), **freeze a dated snapshot** and build charts + prose from it. WordCamp Central is live, so small day-to-day changes (105 → 107 events) otherwise read as false "drift."

## Open tasks for whoever adopts this

1. Write `assemble.py` to merge the three feeds into `dashboard_data.json` (removes the last manual step besides the browser pull).
2. Turn the browser pull (step 5) into a small documented helper.
3. Add GatherPress (events.wordpress.org) as a fourth feed when it goes live; the data model is source-agnostic.
