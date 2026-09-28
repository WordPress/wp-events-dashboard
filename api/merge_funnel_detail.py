#!/usr/bin/env python3
"""
merge_funnel_detail.py — fold a manual funnel-detail pull into dashboard_data.json.

The per-event funnel detail (and momentum) can't be fetched by the automated job;
they come from api/pull_funnel_detail.js run in a logged-in Central browser session.
This script takes that downloaded funnel_detail.json and updates the dashboard's
pipeline.records (+ testCount, detailAsOf). Momentum is left as-is unless the JSON
includes a "momentum" object.

Usage:
    python3 api/merge_funnel_detail.py funnel_detail.json
    # then:  python3 build_dashboard.py && cp events-dashboard.html index.html
    #        git add dashboard_data.json events-dashboard.html events-dashboard.artifact.html index.html
    #        git commit -m "Refresh funnel detail" && git push
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, "..", "dashboard_data.json")

# Same list as assemble.py's PUBLIC_RECORD_FIELDS. Keep them in step.
PUBLIC_RECORD_FIELDS = ("id", "slug", "stage", "title", "start", "location",
                        "anticipated", "link", "format", "country", "us",
                        "modified", "test")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 api/merge_funnel_detail.py funnel_detail.json"); sys.exit(1)
    src = sys.argv[1]
    if not os.path.exists(src):
        print("Not found:", src); sys.exit(1)
    payload = json.load(open(src))
    incoming = payload.get("records", [])
    if not incoming:
        print("No records in", src, "- aborting (nothing to merge)."); sys.exit(1)
    asof = payload.get("asOf")

    d = json.load(open(DASH))
    p = d.setdefault("pipeline", {})
    # Keep only fields that are safe to publish. These records are applications
    # Central keeps private (vetting, orientation, on hold...), and everything in
    # dashboard_data.json is embedded into the public index.html whether or not
    # the page displays it. An allowlist, so a new field in an older or newer
    # copy of pull_funnel_detail.js (e.g. an organizer name) never ships by default.
    live = [{k: r[k] for k in PUBLIC_RECORD_FIELDS if k in r}
            for r in incoming if not r.get("test")]
    tests = sum(1 for r in incoming if r.get("test"))

    # --- Preserve last-change dates ('modified') across merges. -----------------
    # 'modified' is what powers the "Needs attention" section (stuck-for-3+-months).
    # An OUT-OF-DATE copy of pull_funnel_detail.js omits it; without this guard,
    # re-running such a copy silently wipes the field and the section disappears.
    # So: if an incoming record lacks 'modified', carry it over from the previous
    # merge (matched by id), and warn loudly if most records are missing it.
    prev_mod = {str(r.get("id")): r.get("modified")
                for r in (p.get("records") or []) if r.get("modified")}
    incoming_mod = sum(1 for r in live if r.get("modified"))   # before any carry-over
    carried = 0
    for r in live:
        if not r.get("modified") and prev_mod.get(str(r.get("id"))):
            r["modified"] = prev_mod[str(r.get("id"))]
            carried += 1
    with_mod = sum(1 for r in live if r.get("modified"))       # after carry-over

    p["records"] = live
    p["testCount"] = tests
    if asof:
        p["detailAsOf"] = asof
    if isinstance(payload.get("momentum"), dict) and payload["momentum"]:
        p["momentum"] = payload["momentum"]
    # keep the top-level dates block in sync so the footer is accurate
    d.setdefault("dates", {})["pipelineDetail"] = asof or d.get("dates", {}).get("pipelineDetail")

    json.dump(d, open(DASH, "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(f"Merged {len(live)} funnel records ({tests} test records excluded), detail as of {asof}.")
    print("  by stage:", dict(Counter(r.get("stage") for r in live)))
    if carried:
        print(f"  carried over {carried} last-change date(s) from the previous merge.")
    print(f"  last-change date present on {with_mod}/{len(live)} records.")
    if incoming_mod < len(live) * 0.5:
        print("\n  *** WARNING: this funnel_detail.json is missing the last-change date ***")
        print("  *** ('modified') on most records — it came from an OLD copy of")
        print("  *** api/pull_funnel_detail.js. Re-copy the CURRENT file contents into the")
        print("  *** Central console and re-run to get fresh dates.")
        if carried:
            print(f"  *** (For now, {carried} date(s) were carried over from the last merge,")
            print("  *** so the 'Needs attention' section is preserved but not fully current.)\n")
        else:
            print("  *** The 'Needs attention' section will be empty until this is fixed.\n")
    print("Next: python3 build_dashboard.py && cp events-dashboard.html index.html, then commit + push.")

if __name__ == "__main__":
    main()
