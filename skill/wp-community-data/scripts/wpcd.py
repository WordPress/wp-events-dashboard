#!/usr/bin/env python3
"""wpcd: answer WordPress community questions from public data. Stdlib only, Python 3.8+.

  python3 wpcd.py meetups   --country USA --months 8 --in-person
  python3 wpcd.py wordcamps --country US --from 2022 --to 2026 --in-person --by-community
  python3 wpcd.py freshness

Sources (all public, no login):
  Meetup groups:  https://wordpress.github.io/wp-events-dashboard/dashboard_data.json
  WordCamps:      https://central.wordcamp.org/wp-json/wp/v2/wordcamps
Add --format csv|json|md (default md). Run any command with -h for options.
"""
import argparse, csv, datetime as dt, html, json, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

DASH = "https://wordpress.github.io/wp-events-dashboard/dashboard_data.json"
CENTRAL = "https://central.wordcamp.org/wp-json/wp/v2/wordcamps"
UA = {"User-Agent": "wp-community-data-skill/1.0"}
TODAY = dt.date.today()

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.loads(r.read()), r.headers

def emit(rows, cols, fmt, note=""):
    if fmt == "json":
        print(json.dumps({"note": note, "count": len(rows), "rows": rows}, indent=1)); return
    if fmt == "csv":
        w = csv.DictWriter(sys.stdout, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows); return
    if note: print(note + "\n")
    print("| " + " | ".join(cols) + " |"); print("|" + "---|" * len(cols))
    for r in rows:
        print("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |")
    print("\n%d rows" % len(rows))

# ---------- meetups ----------
def meetups(a):
    d, _ = get(DASH); m = d["meetups"]; groups = m["allGroups"]
    if a.country and a.country.strip().lower() in ("us", "u.s.", "united states", "united states of america"):
        a.country = "USA"
    windowed = bool(a.since or a.months is not None or not (a.group or a.status))
    since = a.since or (TODAY - dt.timedelta(days=round((a.months or 6) * 30.44))).isoformat()
    has_ip = any(g.get("lastInPerson") for g in groups)
    field = "last"
    note = "Meetup data as of %s." % d["dates"].get("meetups", "?")
    if windowed: note += " Window: met on or after %s." % since
    if a.in_person and windowed:
        if has_ip:
            field = "lastInPerson"; note += " In person only (hybrid counts as in person)."
        else:
            note = ("NOT IN-PERSON DATA. The dashboard does not publish in-person dates yet, so this list is"
                    " groups that met AT ALL (online included). Tell the person that, in those words, before"
                    " the list. " + note)
    rows = []
    for g in groups:
        if a.country and g.get("country", "").lower() != a.country.lower(): continue
        if a.group and a.group.lower() not in (g.get("group", "") + " " + g.get("city", "")).lower(): continue
        if a.status and g.get("cat", "").lower() != a.status.lower(): continue
        if windowed and (not g.get(field) or g[field] < since): continue
        rows.append({"group": g["group"], "city": g.get("city", ""), "country": g.get("country", ""),
                     "members": g.get("members", 0), "last_any": g.get("last", ""),
                     "last_in_person": g.get("lastInPerson", "") or ("n/a" if not has_ip else ""),
                     "in_person_365d": g.get("inPerson365", "") if g.get("inPerson365") is not None else "",
                     "status": g.get("cat", ""), "url": g.get("url", ""),
                     "organizers": ", ".join(l["n"] for l in g.get("leaders", [])) if a.organizers else ""})
    if windowed:
        rows.sort(key=lambda r: (r["last_in_person"] if has_ip and a.in_person else r["last_any"]), reverse=True)
    else:
        rows.sort(key=lambda r: r["members"], reverse=True)
    cols = ["group", "city", "country", "members", "last_any"] + (["last_in_person", "in_person_365d"] if has_ip else []) + ["status", "url"]
    if not rows and a.group and windowed:
        note += " Nothing matching %r met in that window. Drop --months and --since to see the group anyway." % a.group
    elif not rows and a.group:
        note += " No group name or city contains %r. Try a shorter part of the name." % a.group
    elif not rows and a.country:
        known = sorted({g.get("country", "") for g in groups if g.get("country")})
        note += " No rows. Country names here are written like: " + ", ".join(known[:12]) + " ..."
    total = sum(1 for g in groups if not a.country or g.get("country", "").lower() == a.country.lower())
    note += " %d of %d groups%s match." % (len(rows), total, " in " + a.country if a.country else "")
    if a.organizers: cols.append("organizers")
    emit(rows, cols, a.format, note)

# ---------- wordcamps ----------
def central_all(statuses):
    out = []
    for st in statuses:
        q = lambda p: CENTRAL + "?" + urllib.parse.urlencode({"per_page": 100, "page": p, "status": st})
        first, h = get(q(1)); out += first
        pages = int(h.get("X-WP-TotalPages", "1"))
        if pages > 1:
            with ThreadPoolExecutor(max_workers=8) as ex:
                for chunk in ex.map(lambda p: get(q(p))[0], range(2, pages + 1)): out += chunk
    return out

def kind(title):
    s = title.lower()
    if any(k in s for k in ("wordcamp us", "wordcamp europe", "wordcamp asia")): return "Flagship WordCamp"
    if "campus connect" in s: return "Campus Connect"
    if "wordcamp" in s: return "WordCamp"
    if "women" in s and ("wordpress" in s or "wp" in s): return "Women WordPress Day"
    if "wordpress day" in s: return "WordPress Day"
    return "Other community event"

STATES = ("alabama alaska arizona arkansas california colorado connecticut delaware florida georgia hawaii idaho "
          "illinois indiana iowa kansas kentucky louisiana maine maryland massachusetts michigan minnesota "
          "mississippi missouri montana nebraska nevada ohio oklahoma oregon pennsylvania tennessee texas utah "
          "vermont virginia washington wisconsin wyoming").split() + ["new hampshire", "new jersey", "new mexico",
          "new york", "north carolina", "north dakota", "rhode island", "south carolina", "south dakota", "west virginia"]

def community_of(title, kind_, city):
    """'WordCamp Montclair New Jersey 2024' -> 'Montclair'. Flagships keep their name plus host city."""
    import re
    t = re.sub(r"\b(19|20)\d\d\b", "", title)
    t = re.sub(r"(?i)\bwordcamp\b", "", t).strip(" ,-")
    if kind_ == "Flagship WordCamp":
        return "WordCamp %s (%s)" % (t, city) if city else "WordCamp " + t
    t = t.split(",")[0].strip()
    t = re.sub(r"(?i)\s+(usa|us|united states)$", "", t)
    for st in sorted(STATES, key=len, reverse=True):
        t = re.sub(r"(?i)\s+%s$" % re.escape(st), "", t)
    return t.strip() or city

def is_country(r, want):
    if not want: return True
    w = want.lower()
    code = (r.get("_venue_country_code") or r.get("_host_country_code") or "").lower()
    name = (r.get("_venue_country_name") or r.get("_host_country_name") or "").lower()
    loc = (r.get("Location") or "").lower()
    aliases = {"us": ["us", "usa", "united states", "united states of america"]}.get(w, [w])
    if w in ("usa", "united states"): aliases = ["us", "usa", "united states", "united states of america"]
    return code in aliases or name in aliases or any(loc.endswith(", " + x) or loc.endswith(" " + x) for x in aliases)

def wordcamps(a):
    if a.upcoming:
        statuses = ["wcpt-scheduled"]
        a.year_from = TODAY.year if a.year_from is None else a.year_from
        a.year_to = TODAY.year + 10 if a.year_to is None else a.year_to
    else:
        statuses = ["wcpt-scheduled", "wcpt-closed"] + (["wcpt-cancelled"] if a.include_cancelled else [])
        a.year_from = TODAY.year - 4 if a.year_from is None else a.year_from
        a.year_to = TODAY.year if a.year_to is None else a.year_to
    rows = []
    for r in central_all(statuses):
        v = r.get("Start Date (YYYY-mm-dd)")
        try: d = dt.datetime.fromtimestamp(int(v), dt.timezone.utc).date()
        except Exception: continue
        if not (a.year_from <= d.year <= a.year_to): continue
        if a.upcoming and d < TODAY: continue
        if not is_country(r, a.country): continue
        title = html.unescape((r.get("title") or {}).get("rendered", ""))
        k = kind(title)
        if not a.all_types and k not in ("WordCamp", "Flagship WordCamp"): continue
        virtual = bool(r.get("Virtual event only"))
        if a.in_person and virtual: continue
        city = r.get("_venue_city") or r.get("_host_city") or (r.get("Location") or "").split(",")[0]
        rows.append({"date": d.isoformat(), "title": title, "type": k,
                     "community": community_of(title, k, (r.get("_venue_city") or "").strip()), "location": r.get("Location", ""),
                     "city": city.strip(), "state": r.get("_venue_state") or r.get("_host_state") or "",
                     "format": "online" if virtual else "in person",
                     "status": r.get("status", "").replace("wcpt-", ""), "url": r.get("URL") or r.get("link", "")})
    rows.sort(key=lambda r: r["date"])
    span = "upcoming from %s" % TODAY.isoformat() if a.upcoming else "%d to %d" % (a.year_from, a.year_to)
    note = "WordCamp Central, %s%s%s. Status 'closed' = happened; 'scheduled' = upcoming. Only events Central lists publicly; applications still in planning are not included." % (
        span, ", " + a.country if a.country else "", ", in person only" if a.in_person else "")
    if a.by_community:
        by = {}
        for r in rows:
            key = (r["community"], r["state"])
            e = by.setdefault(key, {"community": key[0], "state": key[1], "events": 0, "years": set(), "titles": [],
                                    "kind": "flagship" if r["type"] == "Flagship WordCamp" else "local"})
            e["events"] += 1; e["years"].add(r["date"][:4]); e["titles"].append(r["title"])
        out = [{"community": e["community"], "kind": e["kind"], "state": e["state"], "events": e["events"],
                "years": ", ".join(sorted(e["years"])), "titles": "; ".join(e["titles"])}
               for e in sorted(by.values(), key=lambda e: (e["kind"] == "flagship", -e["events"], e["community"]))]
        locals_ = sum(1 for o in out if o["kind"] == "local")
        note += " %d local communities, then %d flagship rows (WordCamp US moves city each year)." % (locals_, len(out) - locals_)
        emit(out, ["community", "kind", "state", "events", "years", "titles"], a.format, note); return
    emit(rows, ["date", "title", "type", "location", "format", "status", "url"], a.format, note)

def freshness(a):
    d, _ = get(DASH)
    has_ip = any(g.get("lastInPerson") for g in d["meetups"]["allGroups"])
    print(json.dumps({"dashboard_dates": d.get("dates"), "groups": len(d["meetups"]["allGroups"]),
                      "in_person_dates_published": has_ip}, indent=1))

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("meetups", help="Meetup groups that met recently")
    m.add_argument("--country", help='Country name as the dashboard writes it, e.g. "USA", "Canada", "Mexico"')
    m.add_argument("--months", type=float, help="Met within this many months (default 6)")
    m.add_argument("--since", help="YYYY-MM-DD, overrides --months")
    m.add_argument("--group", help="Part of a group name or city. Finds the group however long ago it met")
    m.add_argument("--status", choices=["Active", "Fading", "Inactive", "Never"], type=str.capitalize,
                   help="Only groups in this activity status, largest first")
    m.add_argument("--in-person", action="store_true"); m.add_argument("--organizers", action="store_true",
                   help="Add organizer names (public on meetup.com). Only when the question needs them.")
    w = sub.add_parser("wordcamps", help="WordCamps (and other Central events) by year and place")
    w.add_argument("--country", help='e.g. "US", "USA", "Canada"')
    w.add_argument("--from", dest="year_from", type=int, help="First year (default: 4 years ago)")
    w.add_argument("--to", dest="year_to", type=int, help="Last year (default: this year)")
    w.add_argument("--upcoming", action="store_true", help="Only scheduled events from today on")
    w.add_argument("--in-person", action="store_true")
    w.add_argument("--all-types", action="store_true", help="Include Campus Connect, WordPress Days, etc.")
    w.add_argument("--include-cancelled", action="store_true"); w.add_argument("--by-community", action="store_true")
    sub.add_parser("freshness", help="When each source was last refreshed")
    for s in (m, w): s.add_argument("--format", choices=["md", "csv", "json"], default="md")
    a = p.parse_args()
    {"meetups": meetups, "wordcamps": wordcamps, "freshness": freshness}[a.cmd](a)

if __name__ == "__main__":
    main()
