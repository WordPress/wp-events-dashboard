/* ============================================================================
 * pull_funnel_detail.js  —  MANUAL browser pull of funnel detail + momentum
 * ----------------------------------------------------------------------------
 * The per-event funnel detail (which events are at each stage) and the monthly
 * momentum are NOT available to the Application Password / GitHub Actions — they
 * need a logged-in browser session. This snippet pulls both.
 *
 * HOW TO RUN
 *   1. Log in to https://central.wordcamp.org with your admin account.
 *   2. Open any wp-admin page there, e.g. https://central.wordcamp.org/wp-admin/
 *   3. Open DevTools console (F12 / Cmd-Opt-J), paste this whole file, Enter.
 *   4. It downloads "funnel_detail.json". Move it into the repo root and run:
 *        python3 api/merge_funnel_detail.py funnel_detail.json
 *
 * MOMENTUM NOTE: newApps (from creation date) and closed (from event date) are
 * exact; confirmed, cancelled, and declined are approximate (derived from the
 * last-modified date, the closest signal to when an event changed status).
 * ==========================================================================*/
(async () => {
  const nonce = (window.wpApiSettings && wpApiSettings.nonce) || null;
  if (!nonce) { console.error("No REST nonce found. Run on a central.wordcamp.org/wp-admin page while logged in."); return; }

  const FUNNEL = [
    ["wcpt-needs-vetting", "Needs Vetting"], ["wcpt-needs-orientati", "Needs Orientation/Interview"],
    ["wcpt-more-info-reque", "On Hold (more info)"], ["wcpt-interview-sched", "Interview Scheduled"],
    ["wcpt-approved-pre-pl", "Approved for Pre-Planning"], ["wcpt-pre-planning", "In Pre-Planning"],
    ["wcpt-needs-budget-re", "Needs Budget Review"], ["wcpt-budget-rev-sche", "Budget Review Scheduled"],
    ["wcpt-needs-contract", "Needs Contract"], ["wcpt-needs-fill-list", "Needs Listing"],
    ["wcpt-needs-schedule", "Needs Schedule"],
  ];
  const fmtType = (t) => {
    const s = (t || "").toLowerCase();
    if (s.includes("campus connect")) return "Campus Connect";
    if (s.includes("student club")) return "Student Club";
    if (s.includes("do_action") || s.includes("doaction")) return "do_action";
    if (s.includes("women") && (s.includes("wordpress") || s.includes("wp"))) return "Women WP Day";
    if (s.includes("wordcamp")) return "WordCamp";
    return "Other";
  };
  const YEAR = String(new Date().getFullYear());
  const monthOf = (iso) => (iso || "").slice(0, 7);
  const startMonth = (ts) => ts ? new Date(+ts * 1000).toISOString().slice(0, 7) : "";
  const get = (url) => fetch(url, { credentials: "include", headers: { "X-WP-Nonce": nonce } });

  const recs = [];       // active-funnel per-event detail (the outreach list)
  const flow = [];       // {created, modified, startMonth, status, test} for momentum

  // 1) active funnel — needs context=edit (that's why this must run in a session)
  for (const [slug, stage] of FUNNEL) {
    let page = 1;
    while (true) {
      const res = await get(`/wp-json/wp/v2/wordcamps?status=${slug}&per_page=100&page=${page}&context=edit`);
      if (!res.ok) { if (res.status === 400 && page > 1) break; console.warn(slug, "->", res.status); break; }
      const batch = await res.json();
      if (!Array.isArray(batch) || !batch.length) break;
      for (const r of batch) {
        const title = (r.title && (r.title.rendered || r.title.raw)) || "";
        const loc = r["Location"] || r["_venue_country_name"] || "";
        const country = (loc.split(",").pop() || "").trim();
        const ts = r["Start Date (YYYY-mm-dd)"];
        const test = /test/i.test(title);
        recs.push({ id: r.id, slug, stage, title, start: ts ? new Date(+ts * 1000).toISOString().slice(0, 10) : null,
          // No organizer name: these are applications Central does not publish, and
          // this output ships in the public repo and on the public Pages site.
          location: loc, anticipated: r["Number of Anticipated Attendees"] || "",
          link: r.link || "", format: fmtType(title), country, us: /(usa|united states)/i.test(country), modified: (r.modified || "").slice(0, 10), test });
        flow.push({ created: monthOf(r.date), modified: monthOf(r.modified), startMonth: startMonth(ts), status: slug, test });
      }
      if (batch.length < 100) break;
      page++;
    }
  }

  // 2) confirmed/closed/lost — recent only (stop once a page is all pre-this-year)
  for (const status of ["wcpt-scheduled", "wcpt-closed", "wcpt-cancelled", "wcpt-rejected"]) {
    let page = 1;
    while (page <= 12) {
      const res = await get(`/wp-json/wp/v2/wordcamps?status=${status}&per_page=100&page=${page}&orderby=modified&order=desc&context=edit`);
      if (!res.ok) break;
      const batch = await res.json();
      if (!Array.isArray(batch) || !batch.length) break;
      let recent = false;
      for (const r of batch) {
        const title = (r.title && (r.title.rendered || r.title.raw)) || "";
        const ts = r["Start Date (YYYY-mm-dd)"];
        const mo = monthOf(r.modified), cr = monthOf(r.date), sm = startMonth(ts);
        if (mo.startsWith(YEAR) || cr.startsWith(YEAR) || sm.startsWith(YEAR)) recent = true;
        flow.push({ created: cr, modified: mo, startMonth: sm, status, test: /test/i.test(title) });
      }
      if (!recent) break;
      if (batch.length < 100) break;
      page++;
    }
  }

  // 3) monthly momentum for this year
  const M = {};
  const bump = (m, k) => { if (!m || !m.startsWith(YEAR)) return; (M[m] = M[m] || { newApps: 0, confirmed: 0, closed: 0, cancelled: 0, declined: 0 })[k]++; };
  for (const e of flow) {
    if (e.test) continue;
    bump(e.created, "newApps");                                            // exact: entered funnel
    if (e.status === "wcpt-scheduled" || e.status === "wcpt-closed") bump(e.modified, "confirmed"); // approx
    if (e.status === "wcpt-closed") bump(e.startMonth, "closed");          // exact-ish: happened
    if (e.status === "wcpt-cancelled") bump(e.modified, "cancelled");      // approx (last-change date)
    if (e.status === "wcpt-rejected") bump(e.modified, "declined");        // approx (last-change date)
  }
  const momentum = {}; Object.keys(M).sort().forEach(k => momentum[k] = M[k]);

  const out = { asOf: new Date().toISOString().slice(0, 10), records: recs, momentum };
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "funnel_detail.json"; a.click();
  console.log(`Pulled ${recs.length} funnel records + ${Object.keys(momentum).length} momentum months (as of ${out.asOf}). Saved funnel_detail.json — now run: python3 api/merge_funnel_detail.py funnel_detail.json`);
})();
