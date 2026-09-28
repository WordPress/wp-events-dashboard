#!/usr/bin/env python3
"""
pull_status_report.py -- read WordCamp Central's PUBLIC WordCamp Status report.

Source: https://central.wordcamp.org/reports/wordcamp-status-report/
(no login). For a given year it lists every WordCamp whose status changed that
year, with a dated log of each change ("2026-08-05: On Hold -> Cancelled").
No organizer names or contact details are in it.

Why this exists: the pipeline detail and the monthly momentum chart come from a
manual browser pull (api/pull_funnel_detail.js), because the Application
Password the nightly job uses can count pre-public applications but not read
them. This report is public, so it can run in GitHub Actions with no secret.

Usage:
  python3 api/pull_status_report.py            # write status_report.json
  python3 api/pull_status_report.py --check    # also compare with dashboard_data.json

What it is good for, measured 2026-09-28 against the 2026-09-11 manual pull:
  - newApps per month (the "Application -> Needs Vetting" entry): within 0-4 of
    the manual pull for every complete month. Exact date of entry, not estimated.
  - cancelled / declined per month: close. These use the date of the actual
    status change, where the manual pull estimates from the last-modified date.
  - confirmed per month: differs from the manual pull, which also estimates it
    from last-modified. Neither is proven right yet.
What it is NOT good for, same measurement:
  - the per-event list. Only 51 of the 94 in-flight records matched both by
    name and by stage. 27 had no exact name match, and 16 matched by name but
    the log's latest entry disagreed with the record's stage, because not every
    status change is written to the log. Per-stage totals also drift from the
    API counts (for example On Hold: hundreds of pre-2020 "More Info Requested"
    camps the API no longer counts). Do not publish a per-event list from this
    alone.

Two traps, both handled below:
  - The status shown next to each camp's name is its status at the END OF THAT
    REPORT'S YEAR, not today. Current status comes from the latest log entry
    across all years.
  - Status labels changed over time ("More Info Requested" is today's "On Hold",
    "Approved For Pre-Planning" is today's "Approved for Pre-Planning Pending
    Agreement"). STAGE maps every label seen so far to the dashboard's stages.
"""
import datetime, html, json, os, re, sys, urllib.request
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "status_report.json")
DASH = os.path.join(HERE, "..", "dashboard_data.json")
URL = ("https://central.wordcamp.org/reports/wordcamp-status-report/"
       "?report-year={year}&period=all&status=any&action=Show+results")
FIRST_YEAR = 2015          # the earliest year the report returns any camps
UA = "wp-events-dashboard (github.com/WordPress/wp-events-dashboard)"

# Report label (any era) -> the dashboard's funnel stage (pull_pipeline.FUNNEL labels).
STAGE = {
    "Needs Vetting": "Needs Vetting",
    "Needs Orientation/Interview": "Needs Orientation/Interview",
    "Needs Orientation": "Needs Orientation/Interview",
    "On Hold": "On Hold (more info)",
    "More Info Requested": "On Hold (more info)",
    "Interview/Orientation Scheduled": "Interview Scheduled",
    "Approved for Pre-Planning Pending Agreement": "Approved for Pre-Planning",
    "Approved For Pre-Planning": "Approved for Pre-Planning",
    "In Pre-Planning": "In Pre-Planning",
    "Needs Budget Review": "Needs Budget Review",
    "Budget Review Scheduled": "Budget Review Scheduled",
    "Needs Contract to be Signed": "Needs Contract",
    "Needs to Fill Out WordCamp Listing": "Needs Listing",
    "Needs to be Added to Official Schedule": "Needs Schedule",
}
ENTERED = {"Application", "auto-draft"}            # "from" state of a new application
CONFIRMED = {"WordCamp Scheduled"}
CANCELLED = {"Cancelled", "Cancelada"}
DECLINED = {"Declined", "已拒絕"}

# Anchored name -> its own </p> -> its own <ul>, so a camp with no log can't
# borrow the next camp's.
CAMP = re.compile(r'<strong class="active-camp">(.*?)</strong>[^<]*</p>\s*'
                  r'<ul class="status-log[^"]*">(.*?)</ul>', re.S)
ENTRY = re.compile(r"<li>(\d{4}-\d{2}-\d{2}):\s*(.*?)\s*&rarr;\s*(.*?)</li>")


def fetch(year):
    req = urllib.request.Request(URL.format(year=year), headers={"User-Agent": UA})
    page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    start = page.find('class="report-results"')
    if start == -1:
        sys.exit(f"{year}: no report-results block -- the report page changed shape")
    return page[start:]


def parse(page):
    for name, log in CAMP.findall(page):
        yield (html.unescape(name).strip(),
               [(d, html.unescape(a).strip(), html.unescape(b).strip())
                for d, a, b in ENTRY.findall(log)])


def pull(this_year):
    camps = defaultdict(set)
    for year in range(FIRST_YEAR, this_year + 1):
        for name, log in parse(fetch(year)):
            camps[name].update(log)
    return {name: sorted(log) for name, log in camps.items() if log}


def momentum(camps, year):
    m = defaultdict(lambda: {"newApps": 0, "confirmed": 0, "cancelled": 0, "declined": 0})
    for log in camps.values():
        for date, frm, to in log:
            if not date.startswith(str(year)):
                continue
            month = date[:7]
            if frm in ENTERED:
                m[month]["newApps"] += 1
            if to in CONFIRMED:
                m[month]["confirmed"] += 1
            if to in CANCELLED:
                m[month]["cancelled"] += 1
            if to in DECLINED:
                m[month]["declined"] += 1
    return {k: m[k] for k in sorted(m)}


def current(camps):
    """Each camp's latest logged status, mapped to a funnel stage (None if not in the funnel)."""
    out = []
    for name, log in camps.items():
        date, _, to = log[-1]
        out.append({"title": name, "status": to, "stage": STAGE.get(to), "lastChange": date})
    return out


def check(result):
    """Compare with what the dashboard currently publishes. Prints only; changes nothing."""
    if not os.path.exists(DASH):
        return
    p = json.load(open(DASH)).get("pipeline", {})
    counts = p.get("funnelCounts", {})
    ours = Counter(c["stage"] for c in result["camps"] if c["stage"])
    print("\nstage                          report    api")
    for stage, n in counts.items():
        print(f"  {stage:28} {ours.get(stage, 0):6} {n:6}")
    by_title = {c["title"]: c for c in result["camps"]}
    recs = p.get("records", [])
    matched = [r for r in recs if html.unescape(r.get("title", "")) in by_title]
    same = sum(1 for r in matched if by_title[html.unescape(r["title"])]["stage"] == r.get("stage"))
    print(f"\nrecords: {len(recs)} published, {len(matched)} found by exact name, "
          f"{same} with the same stage (records as of {p.get('detailAsOf')})")
    old = p.get("momentum", {})
    print("\nmonth     newApps       confirmed     cancelled     declined   (report vs published)")
    for month in sorted(set(old) | set(result["momentum"])):
        a, b = result["momentum"].get(month, {}), old.get(month, {})
        print("  " + month + "".join(f"  {a.get(k, 0):4} vs {b.get(k, 0):<4}"
                                     for k in ("newApps", "confirmed", "cancelled", "declined")))


def main():
    today = datetime.date.today()
    camps = pull(today.year)
    result = {
        "asOf": today.isoformat(),
        "source": "central.wordcamp.org WordCamp Status report (public)",
        "momentum": momentum(camps, today.year),
        "camps": current(camps),
    }
    json.dump(result, open(OUT, "w"), ensure_ascii=False, indent=1)
    in_funnel = sum(1 for c in result["camps"] if c["stage"])
    print(f"{len(camps)} camps with a status log, {in_funnel} whose latest status is a funnel stage "
          f"-> {os.path.relpath(OUT)}")
    if "--check" in sys.argv:
        check(result)


if __name__ == "__main__":
    main()
