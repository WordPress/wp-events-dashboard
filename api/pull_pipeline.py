#!/usr/bin/env python3
"""
WordCamp Central AUTHENTICATED pull — the event pipeline the public API hides.

The public endpoint (pull_events.py) only returns wcpt-scheduled + wcpt-closed.
Authenticated with a WordPress Application Password we can additionally see:
  - FULL DETAIL for cancelled + declined (rejected) events
  - COUNTS for the 11-stage active application funnel (bodies are private, so
    count-only for a non-deputy account; the funnel *shape* still comes through)

Auth: wccentral_secrets.json (git-ignored). Never paste it into chat.
  Generate at https://central.wordcamp.org/wp-admin/profile.php -> Application Passwords.

Usage:
  python3 pull_pipeline.py            # write ../pipeline.json + print the funnel summary
  python3 pull_pipeline.py --funnel   # just print the funnel counts

Status taxonomy discovered on central.wordcamp.org (2026-07):
  the ACTIVE funnel, in workflow order, then the two public statuses, then terminal.
"""
import json, os, sys, base64, datetime, urllib.request, urllib.error, urllib.parse, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SECRETS = os.path.join(HERE, "wccentral_secrets.json")
OUT = os.path.join(HERE, "..", "pipeline.json")
HISTORY = os.path.join(HERE, "..", "history.json")

def bank_history(asof, funnel, scheduled_n, declined_n, cancelled_n):
    """Merge a dated pipeline snapshot into history.json (one row per date,
    shared with the meetup + event metrics banked by the other pullers)."""
    try:
        hist = json.load(open(HISTORY))
    except Exception:
        hist = []
    snap = {
        "funnel": {f["slug"]: f["count"] for f in funnel},
        "activeFunnelTotal": sum(f["count"] for f in funnel),
        "scheduled": scheduled_n,
        "declined": declined_n,
        "cancelled": cancelled_n,
    }
    row = next((h for h in hist if h.get("date") == asof), None)
    if row is None:
        row = {"date": asof}
        hist.append(row)
    row["pipeline"] = snap
    hist.sort(key=lambda h: h["date"])
    json.dump(hist, open(HISTORY, "w"), indent=1)
    return len(hist)

# Active application funnel, in workflow order. (slug, human label)
FUNNEL = [
    ("wcpt-needs-vetting",   "Needs Vetting"),
    ("wcpt-needs-orientati", "Needs Orientation/Interview"),
    ("wcpt-more-info-reque", "On Hold (more info)"),
    ("wcpt-interview-sched", "Interview Scheduled"),
    ("wcpt-approved-pre-pl", "Approved for Pre-Planning"),
    ("wcpt-pre-planning",    "In Pre-Planning"),
    ("wcpt-needs-budget-re", "Needs Budget Review"),
    ("wcpt-budget-rev-sche", "Budget Review Scheduled"),
    ("wcpt-needs-contract",  "Needs Contract"),
    ("wcpt-needs-fill-list", "Needs Listing"),
    ("wcpt-needs-schedule",  "Needs Schedule"),
]
PUBLIC   = [("wcpt-scheduled", "Scheduled"), ("wcpt-closed", "Closed")]
TERMINAL = [("wcpt-rejected", "Declined"), ("wcpt-cancelled", "Cancelled")]
# Statuses whose record bodies this account can actually read (not just count).
READABLE_DETAIL = {"wcpt-scheduled", "wcpt-closed", "wcpt-cancelled", "wcpt-rejected"}

DETAIL_FIELDS = ["id", "status", "title", "link", "Start Date (YYYY-mm-dd)",
                 "End Date (YYYY-mm-dd)", "Location",
                 "Number of Anticipated Attendees", "URL"]

def die(m): print("ERROR:", m); sys.exit(1)

def load_secrets():
    s = json.load(open(SECRETS)) if os.path.exists(SECRETS) else {}
    e = os.environ  # env vars override the file (used by CI / GitHub Actions secrets)
    if e.get("WCCENTRAL_USERNAME"): s["username"] = e["WCCENTRAL_USERNAME"]
    if e.get("WCCENTRAL_APP_PASSWORD"): s["app_password"] = e["WCCENTRAL_APP_PASSWORD"]
    if e.get("WCCENTRAL_BASE_URL"): s["base_url"] = e["WCCENTRAL_BASE_URL"]
    if (not s.get("username") or not s.get("app_password")
            or "PASTE" in s.get("username", "") or "xxxx" in s.get("app_password", "")):
        die("No WordCamp Central credentials: set WCCENTRAL_USERNAME/WCCENTRAL_APP_PASSWORD (CI) or fill api/wccentral_secrets.json (local).")
    return s

def opener(s):
    tok = base64.b64encode(("%s:%s" % (s["username"], s["app_password"])).encode()).decode()
    base = s.get("base_url", "https://central.wordcamp.org").rstrip("/")
    def call(params):
        url = "%s/wp-json/wp/v2/wordcamps?%s" % (base, urllib.parse.urlencode(params))
        req = urllib.request.Request(url, headers={"Authorization": "Basic " + tok,
                                                   "User-Agent": "yotm-pipeline/1.1"})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read()), r.headers
    return call

def count(call, status):
    try:
        _, hdr = call({"status": status, "per_page": 1})
        return int(hdr.get("X-WP-Total", "0"))
    except urllib.error.HTTPError:
        return 0

def pull_detail(call, status):
    rows, page = [], 1
    while True:
        try:
            batch, _ = call({"status": status, "per_page": 100, "page": page,
                             "_fields": ",".join(DETAIL_FIELDS)})
        except urllib.error.HTTPError as e:
            if e.code == 400 and page > 1: break
            raise
        if not batch: break
        rows += batch
        if len(batch) < 100: break
        page += 1
    return rows

def ts_to_date(v):
    if v in (None, "", 0, "0"): return None
    try: return datetime.datetime.utcfromtimestamp(int(v)).date().isoformat()
    except Exception: return None

def clean(r):
    return {
        "id": r.get("id"),
        "status": r.get("status"),
        "title": (r.get("title") or {}).get("rendered", ""),
        "start": ts_to_date(r.get("Start Date (YYYY-mm-dd)")),
        "location": r.get("Location") or "",
        "anticipated": r.get("Number of Anticipated Attendees") or "",
        "link": r.get("link") or "",
    }

def main():
    s = load_secrets()
    call = opener(s)
    asof = datetime.date.today().isoformat()  # header-provided; fine outside the sandbox

    funnel = [{"slug": sl, "label": lb, "count": count(call, sl)} for sl, lb in FUNNEL]
    active_total = sum(f["count"] for f in funnel)
    scheduled_n = count(call, "wcpt-scheduled")

    print("WordCamp pipeline as of %s" % asof)
    print("=" * 48)
    for f in funnel:
        bar = "#" * f["count"]
        print("  %-28s %3d %s" % (f["label"], f["count"], bar))
    print("  %-28s %3d  <- confirmed" % ("Scheduled", scheduled_n))
    declined_n = count(call, "wcpt-rejected")
    cancelled_n = count(call, "wcpt-cancelled")
    print("-" * 48)
    print("  %d WordCamps in the active funnel (pre-scheduled)" % active_total)
    print("  terminal: %d declined, %d cancelled (all-time)" % (declined_n, cancelled_n))

    n = bank_history(asof, funnel, scheduled_n, declined_n, cancelled_n)
    print("  banked pipeline snapshot into history.json (%d snapshots)" % n)

    if "--funnel" in sys.argv:
        return

    print("\nPulling full detail for cancelled + declined (readable)...")
    cancelled = [clean(r) for r in pull_detail(call, "wcpt-cancelled")]
    declined  = [clean(r) for r in pull_detail(call, "wcpt-rejected")]
    scheduled = [clean(r) for r in pull_detail(call, "wcpt-scheduled")]
    print("  cancelled %d · declined %d · scheduled %d" % (len(cancelled), len(declined), len(scheduled)))

    out = {
        "asOf": asof,
        "source": "central.wordcamp.org authenticated REST (Application Password)",
        "funnel": funnel,
        "activeFunnelTotal": active_total,
        "readableNote": "Active-funnel statuses are count-only for this account; "
                        "cancelled/declined/scheduled include full detail.",
        "scheduled": scheduled,
        "cancelled": cancelled,
        "declined": declined,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
