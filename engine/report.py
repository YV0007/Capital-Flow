"""Weekly report: DB -> runs/<week>/weekly_report.md.

Sections: fired themes (the alpha), new verified events, top sectors by capital,
beneficiary map updates, and candidates worth watching.
"""

from . import db


def _fmt_amt(v):
    if v is None:
        return "—"
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


def run(week: str) -> str:
    con = db.connect()
    L = [f"# Capital Flow — Weekly Report {week}", ""]

    themes = con.execute(
        "SELECT theme, rule, strength FROM themes WHERE run_week=? ORDER BY strength DESC",
        (week,)).fetchall()
    L.append("## Signals fired")
    if themes:
        for t in themes:
            L.append(f"- **{t['theme']}**  _(rule: {t['rule']}, strength {t['strength']})_")
    else:
        L.append("_No signal rules fired this week._")
    L.append("")

    new = con.execute(
        """SELECT a.name allocator, e.target, e.sector, e.event_type, e.amount_usd,
                  e.status, e.source_tier, e.source_reliability, e.info_credibility,
                  e.confidence_score
           FROM events e JOIN allocators a ON a.id=e.allocator_id
           WHERE e.run_week=? AND e.status IN ('verified','verified_alpha')
           ORDER BY e.confidence_score DESC, e.amount_usd DESC NULLS LAST""", (week,)).fetchall()
    L.append(f"## New verified events ({len(new)})")
    if new:
        L.append("| Allocator | Target | Sector | Type | Amount | Status | Conf |")
        L.append("|---|---|---|---|--:|---|:-:|")
        for e in new:
            grade = f"{e['source_reliability']}{e['info_credibility']}·{e['confidence_score']}"
            L.append(f"| {e['allocator']} | {e['target']} | {e['sector']} | {e['event_type']} "
                     f"| {_fmt_amt(e['amount_usd'])} | {e['status']} | {grade} |")
    else:
        L.append("_None._")
    L.append("")

    sectors = con.execute(
        """SELECT sector, COUNT(*) n, SUM(COALESCE(amount_usd,0)) total,
                  COUNT(DISTINCT allocator_id) allocs FROM events
           WHERE disclosed_date >= date('now','-30 days')
           GROUP BY sector ORDER BY total DESC LIMIT 10""").fetchall()
    L.append("## Top sectors — last 30 days")
    if sectors:
        L.append("| Sector | Capital | Deals | Distinct allocators |")
        L.append("|---|--:|--:|--:|")
        for s in sectors:
            L.append(f"| {s['sector']} | {_fmt_amt(s['total'])} | {s['n']} | {s['allocs']} |")
    else:
        L.append("_No activity in the last 30 days._")
    L.append("")

    th = con.execute(
        """SELECT theme, COUNT(*) n, SUM(COALESCE(amount_usd,0)) total,
                  COUNT(DISTINCT allocator_id) allocs FROM events
           WHERE theme IS NOT NULL AND disclosed_date >= date('now','-30 days')
           GROUP BY theme ORDER BY total DESC""").fetchall()
    if th:
        L.append("## Themes — last 30 days")
        L.append("| Theme | Capital | Deals | Distinct allocators |")
        L.append("|---|--:|--:|--:|")
        for t in th:
            L.append(f"| {t['theme']} | {_fmt_amt(t['total'])} | {t['n']} | {t['allocs']} |")
        L.append("")

    bens = con.execute(
        """SELECT b.ticker, b.company, b.confidence, a.name allocator, e.target
           FROM beneficiaries b JOIN events e ON e.id=b.event_id
           JOIN allocators a ON a.id=e.allocator_id WHERE e.run_week=?""", (week,)).fetchall()
    if bens:
        L.append(f"## Public beneficiaries mapped ({len(bens)})")
        L.append("| Ticker | Company | From flow | Confidence |")
        L.append("|---|---|---|:-:|")
        for b in bens:
            L.append(f"| {b['ticker']} | {b['company']} | {b['allocator']}→{b['target']} | {b['confidence']} |")
        L.append("")

    cands = con.execute(
        """SELECT a.name allocator, e.target, e.sector, e.event_type FROM events e
           JOIN allocators a ON a.id=e.allocator_id
           WHERE e.run_week=? AND e.status='candidate' ORDER BY e.sector""", (week,)).fetchall()
    L.append(f"## Candidates to watch ({len(cands)})")
    for c in cands:
        L.append(f"- {c['allocator']} → {c['target']} ({c['sector']}, {c['event_type']})")
    if not cands:
        L.append("_None._")
    L.append("")

    # Coverage check (C5/WS2): key & core allocators that produced nothing this run.
    silent = con.execute(
        """SELECT a.name, a.class, a.tier FROM allocators a
           WHERE a.tier IN ('key','core')
             AND NOT EXISTS (SELECT 1 FROM events e
                             WHERE e.allocator_id = a.id AND e.run_week = ?)
           ORDER BY a.tier, a.class, a.name""", (week,)).fetchall()
    total_kc = con.execute(
        "SELECT COUNT(*) FROM allocators WHERE tier IN ('key','core')").fetchone()[0]
    covered = total_kc - len(silent)
    L.append(f"## Coverage — {covered}/{total_kc} key & core allocators produced events")
    if silent:
        L.append(f"_Silent this run ({len(silent)}) — verify these are genuinely quiet, "
                 f"not missed:_")
        L.append("")
        by_class = {}
        for s in silent:
            by_class.setdefault(s["class"], []).append(s["name"])
        for cls, names in sorted(by_class.items()):
            L.append(f"- **{cls}**: {', '.join(names)}")
    else:
        L.append("_Every key & core allocator produced at least one event._")
    L.append("")

    # New allocators discovered co-investing (WS1) — promote to the watchlist.
    disc = con.execute(
        """SELECT name, suggested_class, seen_with, rationale FROM universe_candidates
           WHERE run_week = ? ORDER BY name""", (week,)).fetchall()
    if disc:
        L.append(f"## Discovered allocators — promote to watchlist? ({len(disc)})")
        for d in disc:
            L.append(f"- **{d['name']}** ({d['suggested_class'] or '?'}) — seen with "
                     f"{d['seen_with'] or '—'}. {d['rationale'] or ''}")
        L.append("")

    con.close()
    out = "\n".join(L)
    out_path = db.RUNS_DIR / week / "weekly_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out)
    return str(out_path)


if __name__ == "__main__":
    import sys
    print("wrote", run(sys.argv[1]))
