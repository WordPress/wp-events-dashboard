#!/usr/bin/env python3
"""
assemble.py — merge the three feeds into dashboard_data.json (the single input build_dashboard.py renders).

Inputs it reads:
  data.js          -> meetups (produced by api/pull_meetup.py)
  history.json     -> latest pipeline funnel counts (banked by api/pull_pipeline.py)
  WordCamp Central public REST (live fetch) -> events section
  status_report.json -> pipeline.momentum (from api/pull_status_report.py, Central's public
                       WordCamp Status report); falls back to carry-over if missing or stale
  dashboard_data.json (existing) -> CARRY-OVER of pieces we cannot recompute:
       - meetups.map.land         (baked SVG world outline)
       - events.bench             (from Central's Counts report, not in the public API)
       - pipeline.records         (per-event funnel detail, browser-session only)
       - pipeline.funnelOrder / testCount

Output: dashboard_data.json  (then run build_dashboard.py)

Freshness is tracked per source in the top-level "dates" object so the footer can be honest:
  dates.meetups / dates.events / dates.pipelineCounts are refreshed each run;
  dates.pipelineDetail stays at the last manual browser pull until someone refreshes it.
"""
import json, os, sys, datetime, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_JS   = os.path.join(HERE, "data.js")
HISTORY   = os.path.join(HERE, "history.json")
DASH      = os.path.join(HERE, "dashboard_data.json")
BASELINE  = os.path.join(HERE, "reactivation_baseline.json")
STATUS    = os.path.join(HERE, "status_report.json")
TODAY     = datetime.date.today()
W, H      = 1000, 500

def proj(lat, lon):
    return round((lon + 180) / 360 * W, 1), round((90 - lat) / 180 * H, 1)

# ---------- data.js parsing ----------
def js_block(s, key, op, cl):
    i = s.index(key); b = s.index(op, i); depth = 0
    for j in range(b, len(s)):
        if s[j] == op: depth += 1
        elif s[j] == cl:
            depth -= 1
            if depth == 0: return json.loads(s[b:j+1])
    raise ValueError("could not parse " + key)

def load_meetups_source():
    s = open(DATA_JS).read()
    return (js_block(s, "groups:", "[", "]"),
            js_block(s, "universe:", "{", "}"),
            js_block(s, "meta:", "{", "}"))

def days_since(last, ref):
    if not last: return None
    try: return (ref - datetime.date.fromisoformat(last)).days
    except Exception: return None

def recency_bucket(d):
    if d is None: return "Never met"
    if d <= 30:  return "In the last 30 days"
    if d <= 90:  return "1 to 3 months"
    if d <= 182: return "3 to 6 months"
    if d <= 365: return "6 to 12 months"
    if d <= 730: return "1 to 2 years"
    return "More than 2 years"

RECENCY_ORDER = ["In the last 30 days","1 to 3 months","3 to 6 months","6 to 12 months",
                 "1 to 2 years","More than 2 years","Never met"]

def cat4(d):
    if d is None: return "Never"
    if d <= 90:  return "Active"
    if d <= 365: return "Fading"
    return "Inactive"

STCODE = {"Active": "a", "Dormant": "d", "Not started": "n"}

def build_reactivation(groups, cur_asof):
    """Reactivation scoreboard: compare each group's last-meeting date in the live
    daily data.js against a fixed baseline (reactivation_baseline.json). Reactivated =
    met again after a 90+ day gap; newly quiet = was active at baseline, now fading/inactive.
    Same Meetup source as everything else, just two points in time."""
    if not os.path.exists(BASELINE):
        return None
    base = json.load(open(BASELINE))
    blast = base.get("lastEvent", {})
    b_asof = base.get("asOf")
    def d(s):
        try: return datetime.date.fromisoformat(s) if s else None
        except Exception: return None
    def cat(last, ref):
        x = d(last)
        if not x: return "Never"
        days = (ref - x).days
        return "Active" if days <= 90 else "Fading" if days <= 365 else "Inactive"
    bref, cref = d(b_asof), d(cur_asof)
    react, quiet = [], []
    for g in groups:
        url = g.get("url")
        if not url or url not in blast: continue
        ol, nl = d(blast.get(url)), d(g.get("lastEvent") or "")
        if nl and ol and nl > ol and (nl - ol).days > 90:
            react.append({"group": g.get("group",""), "country": g.get("country",""),
                          "members": int(g.get("members") or 0), "gapDays": (nl - ol).days,
                          "met": g.get("lastEvent"), "url": url})
        elif nl and ol and nl == ol and cat(blast.get(url), bref) == "Active" and cat(g.get("lastEvent"), cref) in ("Fading", "Inactive"):
            quiet.append({"group": g.get("group",""), "country": g.get("country",""),
                          "members": int(g.get("members") or 0), "last": g.get("lastEvent"),
                          "url": url, "cat": cat(g.get("lastEvent"), cref)})
    react.sort(key=lambda x: x["members"], reverse=True)
    quiet.sort(key=lambda x: x["members"], reverse=True)
    return {"from": b_asof, "to": cur_asof, "reactivated": react, "newlyQuiet": quiet,
            "membersBack": sum(r["members"] for r in react)}

def build_meetups(existing):
    groups, uni, meta = load_meetups_source()
    ref = datetime.date.fromisoformat(uni.get("asOf") or TODAY.isoformat())
    for i, g in enumerate(groups):
        g["_i"] = i
        g["_days"] = days_since(g.get("lastEvent") or "", ref)

    rec = {b: 0 for b in RECENCY_ORDER}
    for g in groups: rec[recency_bucket(g["_days"])] += 1
    recency = [[b, rec[b]] for b in RECENCY_ORDER]

    met90   = sum(1 for g in groups if g["_days"] is not None and g["_days"] <= 90)
    toWatch = sum(1 for g in groups if g["_days"] is not None and 90 < g["_days"] <= 365)
    active  = sum(1 for g in groups if g.get("status") == "Active")
    dormant = sum(1 for g in groups if g.get("status") == "Dormant")
    never   = sum(1 for g in groups if g.get("status") == "Not started")
    countries = len({g.get("country") for g in groups if g.get("country")})

    dead = sorted([g for g in groups if (g.get("members") or 0) > 500 and g["_days"] is not None and g["_days"] > 365],
                  key=lambda g: g.get("members") or 0, reverse=True)[:30]
    deadBig = [{"group": g.get("group",""), "city": g.get("city",""), "country": g.get("country",""),
                "members": int(g.get("members") or 0), "last": g.get("lastEvent") or "", "url": g.get("url","")}
               for g in dead]

    us_groups = [g for g in groups if g.get("country") == "USA"]
    us = {"groups": len(us_groups),
          "met90": sum(1 for g in us_groups if g["_days"] is not None and g["_days"] <= 90)}

    allGroups = sorted(
        [{"id": g["_i"], "group": g.get("group",""), "city": g.get("city",""), "country": g.get("country",""),
          "members": int(g.get("members") or 0), "last": g.get("lastEvent") or "", "url": g.get("url",""),
          "leaders": g.get("leaders") or [], "cat": cat4(g["_days"])} for g in groups],
        key=lambda x: x["members"], reverse=True)

    points = []
    for g in groups:
        lat, lon = g.get("lat"), g.get("lon")
        if lat is None or lon is None: continue
        x, y = proj(lat, lon)
        points.append([x, y, STCODE.get(g.get("status"), "n"), g["_i"]])
    counts = {"a": active, "d": dormant, "n": never}
    land = (((existing.get("meetups") or {}).get("map") or {}).get("land")) or ""

    # Groups whose most recent event falls in the current calendar month (the data's
    # asOf month), for the "where the community met this month" map. `count` is every
    # such group; `points` only those we can place on the map (have coords).
    month_key = (uni.get("asOf") or TODAY.isoformat())[:7]
    month_met = [g for g in groups if (g.get("lastEvent") or "")[:7] == month_key]
    month_points = []
    for g in month_met:
        lat, lon = g.get("lat"), g.get("lon")
        if lat is None or lon is None: continue
        x, y = proj(lat, lon)
        month_points.append([x, y, g["_i"]])

    return {
        "asOf": uni.get("asOf") or TODAY.isoformat(),
        "groups": len(groups),
        "members": uni.get("officialMembers") or uni.get("uniqueMembers") or 0,
        "countries": uni.get("officialCountries") or countries,
        "active": active, "dormant": dormant, "never": never,
        "met90": met90, "organizers": uni.get("organizersAllRoles") or uni.get("organizers") or 0,
        "recency": recency, "deadBig": deadBig, "toWatch": toWatch, "us": us,
        "map": {"land": land, "points": points, "counts": counts, "w": W, "h": H},
        "monthMap": {"month": month_key, "points": month_points, "count": len(month_met)},
        "reactivation": build_reactivation(groups, uni.get("asOf") or TODAY.isoformat()),
        "allGroups": allGroups,
    }, uni.get("asOf") or TODAY.isoformat()

# ---------- events (live public API) ----------
EV_BASE = "https://central.wordcamp.org/wp-json/wp/v2/wordcamps"
def _fetch_page(p):
    q = urllib.parse.urlencode({"per_page": 100, "page": p})
    req = urllib.request.Request(EV_BASE + "?" + q, headers={"User-Agent": "assemble/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read()), int(r.headers.get("X-WP-TotalPages", "1"))

def fetch_events():
    first, pages = _fetch_page(1)
    rows = list(first)
    if pages > 1:
        with ThreadPoolExecutor(max_workers=15) as ex:
            for pg in ex.map(lambda p: _fetch_page(p)[0], range(2, pages + 1)):
                rows += pg
    return rows

def ev_start(r):
    v = r.get("Start Date (YYYY-mm-dd)")
    if v in (None, "", 0, "0"): return None
    try: return datetime.datetime.utcfromtimestamp(int(v)).date()
    except Exception: return None

def ev_coords(r):
    c = r.get("_venue_coordinates")
    if isinstance(c, dict) and c.get("latitude") not in (None, "") and c.get("longitude") not in (None, ""):
        try: return float(c["latitude"]), float(c["longitude"])
        except Exception: return None
    return None

def ev_code(title):
    s = (title or "").lower()
    if ("wordcamp us" in s) or ("wordcamp europe" in s) or ("wordcamp asia" in s): return "f"
    if "campus connect" in s: return "c"       # split Campus Connect out of 'newer'
    if "wordcamp" in s: return "l"
    return "n"

def ev_typelabel(title, code):
    s = (title or "").lower()
    if code == "f": return "Flagship WordCamp"
    if code == "l": return "WordCamp"
    if "campus connect" in s: return "Campus Connect"
    if "women" in s and ("wordpress" in s or "wp" in s): return "Women WordPress Day"
    if "do_action" in s or "doaction" in s: return "do_action"
    if "student club" in s: return "Student Club"
    if "wordpress day" in s: return "WordPress Day"
    return "Community event"

def ev_format_bucket(title, code):
    if code == "f": return "Flagships"
    if code == "l": return "Local WordCamps"
    s = (title or "").lower()
    if "campus connect" in s: return "Campus Connect"
    if "women" in s and ("wordpress" in s or "wp" in s): return "Women WP Day"
    return "Other newer"

def build_events(existing):
    rows = fetch_events()
    prev = TODAY.year - 1
    dated = []
    for r in rows:
        d = ev_start(r); st = r.get("status", "")
        title = (r.get("title") or {}).get("rendered", "")
        dated.append({"d": d, "st": st, "title": title, "code": ev_code(title),
                      "coords": ev_coords(r), "loc": r.get("Location") or r.get("_venue_country_name") or "",
                      "country": r.get("_venue_country_name") or "", "link": r.get("link") or ""})
    def live(e): return e["st"] not in ("wcpt-cancelled", "wcpt-rejected")
    y26 = [e for e in dated if e["d"] and e["d"].year == TODAY.year and live(e)]
    ytd = [e for e in y26 if e["d"] <= TODAY]
    prev_ytd = [e for e in dated if e["d"] and e["d"].year == prev and live(e)
                and (e["d"].month, e["d"].day) <= (TODAY.month, TODAY.day)]

    byYear = {}
    for yr in range(2018, TODAY.year + 1):
        f = sum(1 for e in dated if e["d"] and e["d"].year == yr and live(e) and e["code"] == "f")
        l = sum(1 for e in dated if e["d"] and e["d"].year == yr and live(e) and e["code"] == "l")
        c = sum(1 for e in dated if e["d"] and e["d"].year == yr and live(e) and e["code"] == "c")
        n = sum(1 for e in dated if e["d"] and e["d"].year == yr and live(e) and e["code"] == "n")
        byYear[str(yr)] = [f, l, c, n]   # Flagship, Local WordCamp, Campus Connect, New Format

    FORMAT_ORDER = ["Flagships", "Local WordCamps", "Campus Connect", "Women WP Day", "Other newer"]
    fmt = {k: 0 for k in FORMAT_ORDER}
    for e in y26: fmt[ev_format_bucket(e["title"], e["code"])] += 1
    formats = [[k, fmt[k]] for k in FORMAT_ORDER if fmt[k] or k in ("Flagships", "Local WordCamps")]

    # per-country split by category: [country, local, campusConnect, newFormat]
    bycountry = defaultdict(lambda: {"l": 0, "c": 0, "n": 0})
    for e in y26:
        if e["code"] in ("l", "c", "n") and e["country"]:
            bycountry[e["country"]][e["code"]] += 1
    ctot = lambda v: v["l"] + v["c"] + v["n"]
    ranked = sorted(bycountry.items(), key=lambda kv: ctot(kv[1]), reverse=True)[:12]
    if not any(c == "United States" for c, _ in ranked):
        ranked.append(("United States", bycountry.get("United States", {"l": 0, "c": 0, "n": 0})))
    byCountry = [[c, v["l"], v["c"], v["n"]] for c, v in ranked]

    # map: 2026 live events with coords
    points, eventList = [], []
    eord = {"n": 0, "l": 1, "c": 2, "f": 3}   # draw order: newer at bottom, flagship on top
    mcount = {"f": 0, "l": 0, "c": 0, "n": 0}
    for e in sorted([e for e in y26 if e["coords"]], key=lambda e: eord[e["code"]]):
        x, y = proj(*e["coords"]); idx = len(eventList)
        points.append([x, y, e["code"], idx]); mcount[e["code"]] += 1
        eventList.append({"n": e["title"], "loc": e["loc"], "d": e["d"].isoformat(),
                          "ty": ev_typelabel(e["title"], e["code"]), "u": e["link"]})

    # Events that happened, by the month they started. Feeds the "happened" total
    # under the momentum chart, the same basis the manual browser pull used.
    closed = defaultdict(int)
    for e in dated:
        if e["st"] == "wcpt-closed" and e["d"] and e["d"].year == TODAY.year and "test" not in e["title"].lower():
            closed[e["d"].strftime("%Y-%m")] += 1

    bench = (existing.get("events") or {}).get("bench")
    return {
        "closedByMonth": dict(closed),
        "asOf": TODAY.isoformat(),
        "ytd": len(ytd), "ytdPrev": len(prev_ytd), "calendar": len(y26),
        "byYear": byYear, "formats": formats, "byCountry": byCountry,
        "map": {"points": points, "eventList": eventList, "counts": mcount, "w": W, "h": H},
        "bench": bench,
    }, TODAY.isoformat()

# ---------- pipeline (fresh counts + carry-over detail) ----------
FUNNEL = [("wcpt-needs-vetting","Needs Vetting"),("wcpt-needs-orientati","Needs Orientation/Interview"),
    ("wcpt-more-info-reque","On Hold (more info)"),("wcpt-interview-sched","Interview Scheduled"),
    ("wcpt-approved-pre-pl","Approved for Pre-Planning"),("wcpt-pre-planning","In Pre-Planning"),
    ("wcpt-needs-budget-re","Needs Budget Review"),("wcpt-budget-rev-sche","Budget Review Scheduled"),
    ("wcpt-needs-contract","Needs Contract"),("wcpt-needs-fill-list","Needs Listing"),
    ("wcpt-needs-schedule","Needs Schedule")]

def latest_pipeline_snapshot():
    try: hist = json.load(open(HISTORY))
    except Exception: return None
    snaps = sorted([h for h in hist if h.get("pipeline")], key=lambda h: h.get("date",""))
    return (snaps[-1]["date"], snaps[-1]["pipeline"]) if snaps else None

# Pipeline records are applications Central keeps private, and the whole of
# dashboard_data.json is embedded into the public index.html. Only these fields
# are carried forward, so anything else (an organizer name from an older merge)
# is dropped on the next nightly run instead of being republished forever.
# Same list as api/merge_funnel_detail.py. Keep them in step.
PUBLIC_RECORD_FIELDS = ("id", "slug", "stage", "title", "start", "location",
                        "anticipated", "link", "format", "country", "us",
                        "modified", "test")

def public_records(recs):
    return [{k: r[k] for k in PUBLIC_RECORD_FIELDS if k in r} for r in recs or []]

def build_momentum(existing_momentum, closed_by_month):
    """Monthly flow for the momentum chart, from Central's public status report.

    Returns (momentum, as_of). Uses status_report.json only if it was written today,
    so a failed pull can't pass off yesterday's file as fresh; otherwise keeps the
    previous momentum and its date.
    """
    try:
        rep = json.load(open(STATUS))
    except Exception:
        rep = None
    if not rep or rep.get("asOf") != TODAY.isoformat() or not rep.get("momentum"):
        return existing_momentum, None
    months = set(rep["momentum"]) | set(closed_by_month)
    out = {}
    for m in sorted(months):
        row = {"newApps": 0, "confirmed": 0, "cancelled": 0, "declined": 0}
        row.update(rep["momentum"].get(m, {}))
        row["closed"] = closed_by_month.get(m, 0)
        out[m] = row
    return out, rep["asOf"]

def build_pipeline(existing):
    ep = existing.get("pipeline") or {}
    snap = latest_pipeline_snapshot()
    order = [lbl for _, lbl in FUNNEL]
    out = {
        "funnelOrder": order,
        "testCount": ep.get("testCount", 0),
        "records": public_records(ep.get("records")),  # carry-over (browser-only), allowlisted
        "momentum": ep.get("momentum", {}),        # replaced in main() from status_report.json
        "detailAsOf": ep.get("asOf") or ep.get("detailAsOf"),
    }
    if snap:
        cdate, p = snap
        fn = p.get("funnel", {})
        out["funnelCounts"] = {lbl: fn.get(slug, 0) for slug, lbl in FUNNEL}
        out["activeFunnelTotal"] = p.get("activeFunnelTotal", sum(out["funnelCounts"].values()))
        out["scheduledCount"] = p.get("scheduled", ep.get("scheduledCount", 0))
        out["cancelledCount"] = p.get("cancelled", ep.get("cancelledCount", 0))
        out["declinedCount"]  = p.get("declined",  ep.get("declinedCount", 0))
        out["countsAsOf"] = cdate
    else:
        out["funnelCounts"] = {s: 0 for s in order}
        out["activeFunnelTotal"] = len(out["records"])
        out["scheduledCount"] = ep.get("scheduledCount", 0)
        out["cancelledCount"] = ep.get("cancelledCount", 0)
        out["declinedCount"]  = ep.get("declinedCount", 0)
        out["countsAsOf"] = ep.get("asOf")
    return out, out.get("countsAsOf"), out.get("detailAsOf")

def main():
    existing = json.load(open(DASH)) if os.path.exists(DASH) else {}
    print("Assembling dashboard_data.json ...")
    meetups, m_date = build_meetups(existing)
    print(f"  meetups : {meetups['groups']} groups, {meetups['members']:,} members (as of {m_date})")
    if "--no-events" in sys.argv:   # offline mode: keep existing events section
        events = existing.get("events"); e_date = events.get("asOf") if events else None
        print("  events  : skipped (--no-events), kept existing")
    else:
        events, e_date = build_events(existing)
        print(f"  events  : {events['ytd']} YTD / {events['calendar']} on 2026 calendar, {len(events['map']['points'])} mapped (as of {e_date})")
    pipeline, pc_date, pd_date = build_pipeline(existing)
    print(f"  pipeline: {pipeline['activeFunnelTotal']} in funnel (counts as of {pc_date}); detail carried over as of {pd_date}")
    closed = (events or {}).get("closedByMonth", {})
    momentum, mo_date = build_momentum(pipeline["momentum"], closed)
    if mo_date:
        pipeline["momentum"] = momentum
        print(f"  momentum: {len(momentum)} months from the public status report (as of {mo_date})")
    else:
        mo_date = (existing.get("dates") or {}).get("momentum") or pd_date
        print(f"  momentum: status_report.json missing or stale, kept previous (as of {mo_date})")

    out = {
        "asOf": TODAY.isoformat(),
        "dates": {"meetups": m_date, "events": e_date, "pipelineCounts": pc_date,
                  "pipelineDetail": pd_date, "momentum": mo_date},
        "meetups": meetups, "events": events, "pipeline": pipeline,
    }
    json.dump(out, open(DASH, "w"), ensure_ascii=False, indent=1)
    print("wrote", DASH)

if __name__ == "__main__":
    main()
