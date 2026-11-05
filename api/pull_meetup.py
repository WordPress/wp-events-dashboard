#!/usr/bin/env python3
"""
Pull the WordPress Meetup Pro network from the Meetup GraphQL API and refresh the
tracker (../data.js) + a full CSV (../meetup_groups.csv) in one command.

Usage:
  python3 pull_meetup.py --raw     # auth check + dump first page of raw JSON (use this FIRST
                                   # to confirm field names, then we lock the mapping)
  python3 pull_meetup.py           # full pull -> writes ../meetup_groups.csv and rebuilds ../data.js

Secrets live in meetup_secrets.json (git-ignored). Never paste them into chat.
Stdlib only for the access_token path. The JWT path additionally needs PyJWT (pip install pyjwt).
"""
import json, os, sys, datetime, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SECRETS = os.path.join(HERE, "meetup_secrets.json")
DATA_JS = os.path.join(HERE, "..", "data.js")
OUT_CSV = os.path.join(HERE, "..", "meetup_groups.csv")
GQL_URL = "https://api.meetup.com/gql-ext"    # per Meetup API docs
TODAY = datetime.date.today()
ACTIVE_WINDOW = 365

# --- GraphQL query, built to Meetup's documented schema (proNetwork / groupsSearch /
# memberships.totalCount). The `pastEvents` block is the one least-certain field shape;
# if --raw errors mentioning it, paste the error and we swap it in one edit. ---
QUERY = """
query ($urlname: ID!, $cursor: String) {
  proNetwork(urlname: $urlname) {
    groupsSearch(input: { first: 200, after: $cursor, filter: {} }) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id
          name
          urlname
          link
          city
          state
          country
          lat
          lon
          foundedDate
          memberships { totalCount }
          leaders: memberships(first: 12, filter: { status: LEADER }) {
            edges { node { id name memberUrl } }
          }
          groupAnalytics {
            lastEventDate
            totalPastEvents
            averageRsvpsPerEvent
          }
        }
      }
    }
  }
}
"""

# --- ISO alpha-2 country code -> (display name, region). API returns lowercase codes. ---
COUNTRIES = {
  'us':('USA','US/CA'),'ca':('Canada','US/CA'),
  'mx':('Mexico','LATAM'),'br':('Brazil','LATAM'),'ar':('Argentina','LATAM'),'co':('Colombia','LATAM'),
  'cl':('Chile','LATAM'),'ec':('Ecuador','LATAM'),'ve':('Venezuela','LATAM'),'gt':('Guatemala','LATAM'),
  'bo':('Bolivia','LATAM'),'uy':('Uruguay','LATAM'),'py':('Paraguay','LATAM'),'cr':('Costa Rica','LATAM'),
  'do':('Dominican Republic','LATAM'),'pa':('Panama','LATAM'),'pe':('Peru','LATAM'),'ni':('Nicaragua','LATAM'),
  'sv':('El Salvador','LATAM'),'hn':('Honduras','LATAM'),
  'nl':('Netherlands','EU'),'de':('Germany','EU'),'es':('Spain','EU'),'fr':('France','EU'),'it':('Italy','EU'),
  'pl':('Poland','EU'),'gb':('United Kingdom','EU'),'pt':('Portugal','EU'),'se':('Sweden','EU'),'be':('Belgium','EU'),
  'at':('Austria','EU'),'ie':('Ireland','EU'),'dk':('Denmark','EU'),'fi':('Finland','EU'),'no':('Norway','EU'),
  'ch':('Switzerland','EU'),'gr':('Greece','EU'),'cz':('Czech Republic','EU'),'ro':('Romania','EU'),'hu':('Hungary','EU'),
  'bg':('Bulgaria','EU'),'hr':('Croatia','EU'),'rs':('Serbia','EU'),'ua':('Ukraine','EU'),'si':('Slovenia','EU'),
  'sk':('Slovakia','EU'),'lt':('Lithuania','EU'),'ee':('Estonia','EU'),'lv':('Latvia','EU'),'cy':('Cyprus','EU'),
  'al':('Albania','EU'),'mk':('North Macedonia','EU'),'xk':('Kosovo','EU'),'by':('Belarus','EU'),
  'au':('Australia','APAC'),'in':('India','APAC'),'jp':('Japan','APAC'),'id':('Indonesia','APAC'),
  'ph':('Philippines','APAC'),'sg':('Singapore','APAC'),'my':('Malaysia','APAC'),'th':('Thailand','APAC'),
  'vn':('Vietnam','APAC'),'nz':('New Zealand','APAC'),'bd':('Bangladesh','APAC'),'pk':('Pakistan','APAC'),
  'lk':('Sri Lanka','APAC'),'np':('Nepal','APAC'),'tw':('Taiwan','APAC'),'hk':('Hong Kong','APAC'),
  'kr':('South Korea','APAC'),'cn':('China','APAC'),'kh':('Cambodia','APAC'),'bt':('Bhutan','APAC'),'bn':('Brunei','APAC'),
  'ng':('Nigeria','Africa'),'ke':('Kenya','Africa'),'za':('South Africa','Africa'),'gh':('Ghana','Africa'),
  'cm':('Cameroon','Africa'),'ug':('Uganda','Africa'),'tz':('Tanzania','Africa'),'eg':('Egypt','Africa'),
  'ma':('Morocco','Africa'),'zw':('Zimbabwe','Africa'),'rw':('Rwanda','Africa'),'et':('Ethiopia','Africa'),
  'sn':('Senegal','Africa'),'tn':('Tunisia','Africa'),'sz':('Eswatini','Africa'),'cd':('DR Congo','Africa'),
  'lr':('Liberia','Africa'),'tg':('Togo','Africa'),'mg':('Madagascar','Africa'),'ao':('Angola','Africa'),
  'mu':('Mauritius','Africa'),'bf':('Burkina Faso','Africa'),'ga':('Gabon','Africa'),
  'il':('Israel','Other'),'iq':('Iraq','Other'),'tr':('Turkey','Other'),'sa':('Saudi Arabia','Other'),
  'ht':('Haiti','Other'),'jm':('Jamaica','Other'),'ge':('Georgia','Other'),
}
UNKNOWN_CODES = set()
def country_info(code):
    if not code: return ("", "Other")
    hit = COUNTRIES.get(code.lower())
    if hit: return hit
    UNKNOWN_CODES.add(code)
    return (code.upper(), "Other")

def die(msg):
    print("ERROR:", msg); sys.exit(1)

def load_secrets():
    s = json.load(open(SECRETS)) if os.path.exists(SECRETS) else {}
    e = os.environ  # env vars override the file (used by CI / GitHub Actions secrets)
    if e.get("MEETUP_ACCESS_TOKEN"): s["access_token"] = e["MEETUP_ACCESS_TOKEN"]
    for ek, k in [("MEETUP_JWT_CLIENT_ID", "jwt_client_id"),
                  ("MEETUP_JWT_SIGNING_KEY_ID", "jwt_signing_key_id"),
                  ("MEETUP_JWT_AUTHORIZED_MEMBER_ID", "jwt_authorized_member_id"),
                  ("MEETUP_PRO_NETWORK", "pro_network_urlname")]:
        if e.get(ek): s[k] = e[ek]
    if e.get("MEETUP_JWT_PRIVATE_KEY"): s["jwt_private_key"] = e["MEETUP_JWT_PRIVATE_KEY"]  # PEM contents
    if not s:
        die("No Meetup credentials: set env vars (CI) or create api/meetup_secrets.json (local).")
    return s

def get_token(s):
    tok = (s.get("access_token") or "").strip()
    if tok and not tok.startswith("PASTE_"):
        return tok
    # JWT server-to-server fallback (private key from env contents or a file path)
    if s.get("jwt_client_id") and (s.get("jwt_private_key") or s.get("jwt_private_key_path")):
        try:
            import jwt, time
        except ImportError:
            die("JWT path needs PyJWT: pip install pyjwt")
        key = (s["jwt_private_key"].encode() if s.get("jwt_private_key")
               else open(os.path.expanduser(s["jwt_private_key_path"]), "rb").read())
        now = int(time.time())
        assertion = jwt.encode({
            "sub": s["jwt_authorized_member_id"], "iss": s["jwt_client_id"],
            "aud": "api.meetup.com", "exp": now + 120
        }, key, algorithm="RS256", headers={"kid": s["jwt_signing_key_id"]})
        data = urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion
        }).encode()
        req = urllib.request.Request("https://secure.meetup.com/oauth2/access", data=data)
        resp = json.loads(urllib.request.urlopen(req).read())
        return resp["access_token"]
    die("No usable credentials. Put an access_token in meetup_secrets.json (or configure the jwt_* fields).")

ANALYTICS_QUERY = """
query ($urlname: ID!, $since: DateTime!) {
  proNetwork(urlname: $urlname) {
    networkAnalytics { totalGroups totalMembers totalCountries }
    allEvents: eventsSearch(input: { first: 1, filter: {} }) { totalCount }
    recentEvents: eventsSearch(input: { first: 1, filter: { eventDateMin: $since, status: "PAST" } }) { totalCount }
    lowRsvpEvents: eventsSearch(input: { first: 1, filter: { eventDateMin: $since, status: "PAST", rsvpsPerEventMax: 3 } }) { totalCount }
    organizers: membersSearch(input: { first: 1, filter: { roles: ORGANIZER } }) { totalCount }
    allOrganizers: membersSearch(input: { first: 1, filter: { roles: [ORGANIZER, COORGANIZER, ASST_ORGANIZER, EVENT_ORGANIZER] } }) { totalCount }
    activeMembers90d: membersSearch(input: { first: 1, filter: { activeWithinDays: 90 } }) { totalCount }
    activeMembers365d: membersSearch(input: { first: 1, filter: { activeWithinDays: 365 } }) { totalCount }
  }
}
"""

def gql(token, variables, query=None):
    body = json.dumps({"query": query or QUERY, "variables": variables}).encode()
    req = urllib.request.Request(GQL_URL, data=body, headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json"
    })
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        die("HTTP %s from %s\n%s" % (e.code, GQL_URL, e.read().decode()[:1000]))
    if resp.get("errors"):
        die("GraphQL errors:\n" + json.dumps(resp["errors"], indent=2))
    return resp["data"]

# The central chapter-program account is a "leader" of every group; it is not the
# local organizer, so we drop it and keep only the actual local leadership.
CENTRAL_LEADER_ID = "72560962"

def extract_leaders(n):
    out = []
    for e in ((n.get("leaders") or {}).get("edges") or []):
        mm = e.get("node") or {}
        if str(mm.get("id")) == CENTRAL_LEADER_ID:
            continue
        if (mm.get("name") or "").strip().lower() == "wordpress":
            continue
        name = (mm.get("name") or "").strip()
        if not name:
            continue
        out.append({"n": name, "u": mm.get("memberUrl") or ""})
    return out

def node_to_row(n):
    m = (n.get("memberships") or {}).get("totalCount") or 0
    url = n.get("link") or (("https://www.meetup.com/%s/" % n["urlname"]) if n.get("urlname") else "")
    ga = n.get("groupAnalytics") or {}
    le = (ga.get("lastEventDate") or "")[:10]
    pe = ga.get("totalPastEvents") or 0
    rpe = ga.get("averageRsvpsPerEvent") or 0
    cname, creg = country_info(n.get("country") or "")
    if le:
        try: st = "Active" if (TODAY - datetime.date.fromisoformat(le)).days <= ACTIVE_WINDOW else "Dormant"
        except Exception: st = "Dormant"
    else:
        st = "Not started"
    return {
        "group": n.get("name",""), "city": n.get("city",""), "country": cname, "region": creg,
        "lat": n.get("lat"), "lon": n.get("lon"),
        "members": m, "lastEvent": le, "status": st, "platform": "meetup.com",
        "pastEvents": pe, "rsvpsPerEvent": round(rpe, 1),
        "leaders": extract_leaders(n),
        "organizer": "", "reactivation": "—", "url": url,
        "note": ("%d past events · %.0f RSVPs/event" % (pe, rpe)) if pe else ""
    }

def fetch_all(token, urlname):
    rows, cursor = [], None
    while True:
        data = gql(token, {"urlname": urlname, "cursor": cursor})
        gs = ((data or {}).get("proNetwork") or {}).get("groupsSearch") or {}
        edges = gs.get("edges") or []
        for e in edges:
            rows.append(node_to_row(e.get("node") or {}))
        pi = gs.get("pageInfo") or {}
        print("  fetched %d / %s" % (len(rows), gs.get("totalCount","?")))
        if pi.get("hasNextPage") and pi.get("endCursor"):
            cursor = pi["endCursor"]
        else:
            break
    return rows

def existing_universe():
    """Carry over members/events aggregates we can't get from the groups query."""
    try:
        s = open(DATA_JS).read(); i = s.index("universe:"); b = s.index("{", i); d = 0
        for j in range(b, len(s)):
            if s[j] == "{": d += 1
            elif s[j] == "}":
                d -= 1
                if d == 0: return json.loads(s[b:j+1])
    except Exception:
        return {}

HISTORY = os.path.join(HERE, "..", "history.json")

def append_history(rows, official):
    """Bank one dated snapshot per pull so we build our own trend lines.
    Meetup's Insights charts vanish when we migrate off meetup.com; this doesn't."""
    snap = {
        "date": TODAY.isoformat(),
        "groups": len(rows),
        "active": sum(1 for r in rows if r["status"] == "Active"),
        "dormant": sum(1 for r in rows if r["status"] == "Dormant"),
        "neverHosted": sum(1 for r in rows if r["status"] == "Not started"),
        "met90d": sum(1 for r in rows if r["lastEvent"] and
                      (TODAY - datetime.date.fromisoformat(r["lastEvent"])).days <= 90),
        "membershipsSum": sum(int(r.get("members") or 0) for r in rows),
    }
    for k in ("officialMembers", "officialCountries", "officialEvents",
              "events90d", "lowRsvp90", "organizers", "activeMembers90d",
              "activeMembers365d"):
        if (official or {}).get(k) is not None:
            snap[k] = official[k]
    try:
        hist = json.load(open(HISTORY))
    except Exception:
        hist = []
    row = next((h for h in hist if h.get("date") == snap["date"]), None)  # one row per day
    if row is None:
        row = {}
        hist.append(row)
    row.update(snap)  # merge meetup fields, preserving other feeds' keys (e.g. pipeline)
    hist.sort(key=lambda h: h["date"])
    json.dump(hist, open(HISTORY, "w"), indent=1)
    print("history: %d snapshots (%s → %s)" % (len(hist), hist[0]["date"], hist[-1]["date"]))

def write_csv(rows):
    import csv
    cols = ["group","city","country","region","members","last_event_date","platform","organizer","url"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows:
            w.writerow([r["group"], r["city"], r["country"], r["region"], r["members"],
                        r["lastEvent"], r["platform"], r["organizer"], r["url"]])
    print("wrote", OUT_CSV)

def fetch_network_analytics(token, urlname):
    """Meetup's own authoritative totals — the same numbers the Insights page shows."""
    since = (TODAY - datetime.timedelta(days=90)).isoformat() + "T00:00:00Z"
    def c(pn, k):
        return (pn.get(k) or {}).get("totalCount")
    try:
        d = gql(token, {"urlname": urlname, "since": since}, ANALYTICS_QUERY)
        pn = (d or {}).get("proNetwork") or {}
        na = pn.get("networkAnalytics") or {}
        return {
            "officialGroups": na.get("totalGroups"),
            "officialMembers": na.get("totalMembers"),
            "officialCountries": na.get("totalCountries"),
            "officialEvents": c(pn, "allEvents"),
            "events90d": c(pn, "recentEvents"),
            "lowRsvp90": c(pn, "lowRsvpEvents"),
            # "organizers" = everyone holding any organizer role across the network.
            # (roles: ORGANIZER alone returns just the network's primary organizer.)
            "organizers": c(pn, "allOrganizers"),
            "primaryOrganizer": c(pn, "organizers"),
            "activeMembers90d": c(pn, "activeMembers90d"),
            "activeMembers365d": c(pn, "activeMembers365d"),
            "liveAsOf": TODAY.isoformat(),
        }
    except SystemExit:
        return {}

# Fields from the original hand-built data.js that no pull ever refreshes. Carrying
# them forward stamped today's asOf on months-old numbers, so drop them instead.
# Live equivalents: officialMembers (not uniqueMembers), organizers (not organizersAllRoles).
STALE_UNIVERSE_KEYS = ("uniqueMembers", "memberships", "visited90d", "everAttended",
                       "pastEvents", "online90", "organizersAllRoles")

def write_data_js(rows, official=None):
    prev = existing_universe() or {}
    dropped = {k: prev.pop(k) for k in STALE_UNIVERSE_KEYS if k in prev}
    if dropped:
        print("dropped stale universe fields (never refreshed by any pull):", dropped)
    active = sum(1 for r in rows if r["status"] == "Active")
    dormant = sum(1 for r in rows if r["status"] == "Dormant")
    never = sum(1 for r in rows if r["status"] == "Not started")
    countries = len(set(r["country"] for r in rows if r["country"]))
    universe = dict(prev)
    universe.update({
        "asOf": TODAY.isoformat(), "groups": len(rows), "active": active,
        "dormant": dormant, "neverHosted": never, "countries": countries,
        "membershipsSum": sum(int(r.get("members") or 0) for r in rows),
        "source": "Meetup GraphQL API pull, " + TODAY.isoformat(),
        "note": ("officialMembers = Meetup's unique member count (networkAnalytics, same as the "
                 "Insights page). membershipsSum = sum of per-group counts, which double-counts "
                 "anyone in multiple groups. They are different measures; do not mix them."),
    })
    if official:
        universe.update({k: v for k, v in official.items() if v is not None})
    meta = {"updated": TODAY.isoformat(), "owner": "Karen Arnold",
            "note": "Built from a live Meetup GraphQL API pull. Status computed from last event (Active <=365d).",
            "activeWindowDays": ACTIVE_WINDOW}
    sources = [{"name": "Meetup GraphQL API", "detail": "Pulled via api/pull_meetup.py (one-command refresh).", "url": "https://api.meetup.com/gql"}]
    out = ("// WordPress Meetups — data tracker. Live API pull %s.\n"
           "// Single source of truth for index.html; member-level PII excluded.\n"
           "window.MEETUPS = {\n  meta: %s,\n  universe: %s,\n  groups: %s,\n  dataSources: %s\n};\n") % (
        TODAY.isoformat(), json.dumps(meta), json.dumps(universe), json.dumps(rows), json.dumps(sources))
    open(DATA_JS, "w").write(out)
    print("rebuilt", DATA_JS, "with", len(rows), "groups (active %d / dormant %d / never %d)" % (active, dormant, never))

def main():
    s = load_secrets()
    token = get_token(s)
    urlname = s.get("pro_network_urlname", "wordpress")
    if "--raw" in sys.argv:
        data = gql(token, {"urlname": urlname, "cursor": None})
        print(json.dumps(data, indent=2)[:6000])
        print("\n--- auth OK. Eyeball the field names above vs node_to_row(), then run without --raw. ---")
        return
    print("Pulling network:", urlname)
    rows = fetch_all(token, urlname)
    if UNKNOWN_CODES:
        print("NOTE: unmapped country codes (shown as-is, region=Other):", sorted(UNKNOWN_CODES))
    official = fetch_network_analytics(token, urlname)
    if official:
        print("Meetup networkAnalytics (authoritative):", official)
    write_csv(rows)
    write_data_js(rows, official)
    append_history(rows, official)
    print("Done. Reload the dashboard to see the refresh (URLs now in the data).")

if __name__ == "__main__":
    main()
