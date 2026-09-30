# WordPress Community Events Dashboard

A management view of the WordPress community events program: meetups, WordCamps, and the WordCamp application pipeline. Built for DotOrg / Comet + Orion.

**This is deliberately *not* a copy of [events.wordpress.org](https://events.wordpress.org).** That site is the public directory of what's on. This dashboard shows the three things a public listing structurally cannot: the **application pipeline** (what's in flight and where it's stuck), the **decay** (dormant groups, the US-at-zero), and the **trend/synthesis** (2018→2026 trajectory, bench renewal).

> 🌐 **Published publicly** via GitHub Pages at **https://wordpress.github.io/wp-events-dashboard/**. The dashboard data in this repo has been cleared for public release. Note that live API credentials (`api/meetup_secrets.json`, `api/wccentral_secrets.json`) remain git-ignored and must never be committed.

---

## How it stays up to date

A GitHub Action (`.github/workflows/refresh.yml`) runs **every night at 03:13 UTC**, and can also be run by hand from the Actions tab. It:

1. Pulls the Meetup network (`api/pull_meetup.py`).
2. Pulls the WordCamp application **counts** per stage from Central (`api/pull_pipeline.py --funnel`).
3. Merges everything into `dashboard_data.json` (`assemble.py`), including a live read of Central's public events feed.
4. Rebuilds the page (`build_dashboard.py`), copies it to `index.html`, and commits if anything changed. GitHub Pages redeploys on that commit.

Credentials live only in the repo's **Settings → Secrets and variables → Actions**. Each pull step is skipped if its secret is missing, and the dashboard keeps the last data.

**What still needs a person:** the Pipeline tab's event-by-event list and its monthly momentum chart. The nightly job's Application Password can count applications in each stage but can't read them, so that detail comes from a manual pull in a logged-in Central session (step 5 below). Until someone runs it, `assemble.py` carries the last pull forward. The page footer shows the date of each source, and marks the pipeline detail "(manual)" when it's older than the counts.

The bench-renewal numbers on the Events & WordCamps tab come from Central's Counts report, which no script reads yet, so they stay at their last manual value.

---

## Setup

### 0. Just want to look at it?

No setup needed. The dashboard is one self-contained file:

```
open events-dashboard.html
```

It opens in any browser, works offline, and already contains a data snapshot. The nightly job keeps the published copy fresh, so everything below is only for **running a refresh yourself**: testing a change locally, or doing the one manual step.

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
python3 api/pull_pipeline.py --funnel   # -> funnel counts into history.json (needs wccentral_secrets.json)
```

The nightly job runs `pull_meetup.py` and `pull_pipeline.py --funnel`. `pull_events.py` isn't needed for the dashboard itself, since `assemble.py` reads Central's public events feed directly.

### 5. The one manual step: pipeline detail + momentum

The active-funnel **record detail** (which specific ~100 events are in flight) and the monthly **momentum** counts can't be read with the Application Password, so they come from a **logged-in Central browser session**, using an account that can edit WordCamp posts:

1. Log in to https://central.wordcamp.org and open any wp-admin page.
2. Open the browser console, paste the whole of `api/pull_funnel_detail.js`, and press Enter. It downloads `funnel_detail.json`.
3. Move that file into the repo root and run `python3 api/merge_funnel_detail.py funnel_detail.json`.
4. Commit `dashboard_data.json` and push. The next nightly run (or a manual run of the Action) rebuilds the page.

`merge_funnel_detail.py` keeps only fields that are safe to publish, so no organizer names end up in the public data. Weekly at most is plenty.

### 6. Assemble and build

```
python3 assemble.py            # merges the feeds into dashboard_data.json
python3 build_dashboard.py     # renders it
```

`build_dashboard.py` reads `dashboard_data.json` and writes:
- `events-dashboard.html` — standalone, double-click to open
- `events-dashboard.artifact.html` — body-only variant, originally made for publishing as a Claude Artifact

### 7. Publish (GitHub Pages)

The dashboard is served publicly at **https://wordpress.github.io/wp-events-dashboard/**. Pages serves `index.html` from the repo root, which is a copy of the latest `events-dashboard.html`. **The nightly job does this copy and commit for you.** To publish sooner, run the Action by hand from the Actions tab rather than committing a local build, since the bot commits to `main` every night and a hand-built copy can collide with it.

In the repo, **Settings → Pages → Build and deployment → Deploy from a branch → `main` / root** enables hosting.

---

## How the data is wired

`dashboard_data.json` is the single input `build_dashboard.py` renders. `assemble.py` builds it every night from the Meetup pull (`data.js`), the pipeline counts (`history.json`) and a live read of Central's public events feed. A few pieces it can't recompute are carried over from the previous `dashboard_data.json`: the SVG map land outline, the bench-renewal numbers, and the manually pulled pipeline detail and momentum. The top-level `dates` object records when each source was last refreshed, and the page footer shows it.

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

1. Remove the manual browser pull (step 5) so the pipeline detail and momentum refresh nightly too.
2. Read the bench-renewal numbers from a source a script can reach, or label them as a dated snapshot on the page.
3. Add GatherPress (events.wordpress.org) as a fourth feed when it goes live; the data model is source-agnostic.
