"""FUND TRACKER orchestrator (Section 3).

Usage:
  python run_funds.py                     # daily loop: poll, ingest, score, emit
  python run_funds.py --backfill          # FIRST RUN: 8 quarters of 13F per fund
  python run_funds.py --offline           # recompute + re-emit from what is stored
  python run_funds.py --holders           # quarterly: security -> all holders (§8b.5)
  python run_funds.py --deliver           # copy the payload to the dashboard repo

Requires a declared SEC contact header (EDGAR fair-access policy):
  export FUND_SEC_USER_AGENT="Your Name <you@example.com>"

Pipeline:
    seed          config/fund_managers.yaml -> fund_managers, every CIK re-verified
                  against EDGAR's own name for it (a transposed digit silently
                  ingests a stranger's book, so this is a hard gate)
      -> poll     diff every tracked CIK's submissions JSON; new accession = ingest now
      -> 13f      information table -> positions, units DETECTED per filing
      -> fast     13D/G with Item 4 verbatim, Form 3/4/5, material 8-K
      -> ark      the daily full book — zero latency
      -> shorts   NAMED shorts from the FCA/EU registers
      -> watch    §B3 triggers for the four multi-strats (no standing book)
      -> deltas   SHARE-based deltas + conviction scores
      -> audit    §7 — errors block delivery
      -> handoff  handoff/fund_tracker.json (refuses to write a broken file)

Run it daily. It reacts to disclosures, not to the calendar.
"""

import shutil
import sys
from datetime import date

from engine import (fund, fund_13f, fund_ark, fund_audit, fund_crosscheck,
                    fund_deltas, fund_fast, fund_handoff, fund_holders, fund_ident,
                    fund_ingest, fund_sec, fund_sectors, fund_shorts, fund_vehicles,
                    fund_watch)

DELIVER_TO = (fund.db.ROOT.parent / "BASE/Code/ab-investment/src/data/fundTracker.json")


# A daily run should stay quick. The fast-layer queue drains newest-first, so a
# cap keeps a normal run short and lets any backlog clear over the following days
# instead of turning every run into a backfill.
FAST_LAYER_CAP = 250


def main(run_id: str, backfill=False, offline=False, do_adv=False,
         do_crosscheck=False, do_cap_tables=False, deliver=False,
         reparse=False, do_holders=False) -> int:
    print(f"== Fund Tracker: {run_id} ==")
    con = fund.connect()

    # ── seed ────────────────────────────────────────────────────────────────
    verify = None if offline else fund_sec.entity_name
    try:
        s = fund.seed(con, verify_names=verify)
    except fund.FundConfigError as exc:
        print(f"[seed]    CONFIG ERROR — nothing ingested: {exc}")
        return 1
    print(f"[seed]    {s['managers']} tracked + {s['watch_only']} watch-only, "
          f"{s['entities']} filing entities, {s['verified']} CIKs verified vs EDGAR")
    if s["mismatches"]:
        # A CIK that does not resolve to the expected name is not a warning. It
        # means we may be about to ingest somebody else's book under our label.
        print(f"[seed]    HALT — {len(s['mismatches'])} CIK mismatches:")
        for m in s["mismatches"]:
            print("           ", m)
        fund.log_run(con, run_id, "seed", "error", "CIK verification failed",
                     {"mismatches": s["mismatches"]})
        return 1
    fund.log_run(con, run_id, "seed", "ok", "universe seeded and verified", s)

    if reparse:
        n = fund_ingest.reparse(con)
        print(f"[reparse] {n} previously-failed filings requeued")

    if not offline:
        # ── poll ────────────────────────────────────────────────────────────
        p = fund_ingest.poll(con, run_id, backfill=backfill)
        print(f"[poll]    {p['new_filings']} new filings across {p['ciks']} CIKs "
              f"since {p['since']}"
              + ("  [BACKFILL: full history]" if backfill else "")
              + ("  [13F deadline window — polling wide]" if p["deadline_window"] else ""))
        for e in p["errors"][:8]:
            print("           ERR", e)

        # ── 13F backbone ────────────────────────────────────────────────────
        t = fund_13f.ingest_pending(con, run_id)
        print(f"[13f]     {t['positions']} positions from {t['filings']} filings; "
              f"{t['skipped_watch_only']} watch-only filings deliberately not read")
        for f in t["failures"][:8]:
            print("           PARSE FAIL", f)

        # ── fast layer ──────────────────────────────────────────────────────
        cap = None if backfill else FAST_LAYER_CAP
        st = fund_fast.ingest_stakes(con, run_id, limit=cap)
        print(f"[stakes]  {st['stakes']} 13D/G ({st['html_path']} via the weaker "
              f"HTML path), {st['events']} timeline events")
        ins = fund_fast.ingest_insider(con, run_id, limit=cap)
        print(f"[insider] {ins['txns']} exact-dated transactions from "
              f"{ins['filings']} Form 3/4/5")
        k = fund_fast.ingest_8k(con, run_id, limit=cap)
        print(f"[8-k]     {k['events']} material events from {k['filings']} filings")
        sl = fund_ingest.settle_unclaimed(con, run_id)
        print(f"[settle]  {sl['settled']} context filings dispositioned"
              + (f"; {sl['still_pending']} still queued for a stage"
                 if sl["still_pending"] else "; nothing left unaccounted for"))
        am = fund_ingest.flag_amendments(con, run_id)
        print(f"[amend]   {am['amendments']} 13F-HR/A seen — confidential-treatment "
              f"releases flagged loudly")

        # ── daily + register layers ─────────────────────────────────────────
        a = fund_ark.ingest(con, run_id)
        print(f"[ark]     {a['positions']} positions as of {a['as_of']} "
              f"({a['funds']} ETFs, zero disclosure lag)")
        for e in a["errors"][:4]:
            print("           ERR", e)
        sh = fund_shorts.ingest(con, run_id)
        fca = sh.get("FCA", {})
        print(f"[shorts]  {fca.get('current', 0)} current named shorts "
              f"({fca.get('matched', 0)} matched rows); declared gaps: "
              f"{', '.join(sh['declared_gaps']) or '—'}")

        if do_adv:
            adv = fund_vehicles.pull_adv(con, run_id)
            print(f"[adv]     {adv['matched']} ADV records; no registration on file "
                  f"for: {', '.join(adv['no_record']) or '—'} "
                  f"(family-office exemption — a fact, not a gap)")

    # ── vehicles (validated CSV drop) ───────────────────────────────────────
    period = date.today().strftime("%Y-%m")
    v = fund_vehicles.ingest_vehicles(con, run_id, period)
    print(f"[vehicle] {v['holdings']} holdings, {v['nav']} NAV, {v['track']} "
          f"track-record rows"
          + ("" if v["present"] else "  [none supplied — declared as a gap]"))
    for r in v["rejected"][:8]:
        print("           REJECT", r)

    # ── watch-only triggers ─────────────────────────────────────────────────
    w = fund_watch.run(con, run_id, do_cap_tables=do_cap_tables and not offline)
    print(f"[watch]   {w['filings']['fired']} filing triggers, "
          f"{w['shorts']['fired']} short-register triggers"
          + (f", {w['cap_tables']['fired']} cap-table triggers"
             if "cap_tables" in w else ""))

    # ── identifiers, deltas, conviction ─────────────────────────────────────
    n = fund_ident.backfill_tickers(con)
    print(f"[cusip]   {n} previously-unmapped CUSIPs resolved this run")

    # Сектор эмитента из его же SIC на EDGAR. Инкрементально: SIC не меняется,
    # поэтому второй прогон не стоит ни одного запроса.
    if not offline:
        sec = fund_sectors.pull(con, run_id)
        cov = fund_sectors.coverage(con)
        print(f"[sector]  {sec['resolved']}/{sec['requested']} эмитентов "
              f"классифицировано; покрытие книги {cov['classified']}/{cov['securities']} "
              f"бумаг ({cov['pct']}%)")
        for u in sec["unmapped"][:8]:
            print(f"           БЕЗ СЕКТОРА {u}")
        if len(sec["unmapped"]) > 8:
            print(f"           …и ещё {len(sec['unmapped']) - 8}")
        for e in sec["errors"][:5]:
            print(f"           ОШИБКА {e}")
    d = fund_deltas.compute(con, run_id)
    print(f"[deltas]  {d['deltas']} position deltas over {d['periods']} periods, "
          f"{d['events']} new timeline events (share-based, never value-based)")

    if do_holders and not offline:
        # §8b.5 — the reverse lookup. Heavy (a ~100MB quarterly data set), so it is
        # opt-in and quarterly rather than part of the daily loop.
        hs = fund_holders.ingest(con, run_id)
        if hs.get("error"):
            print(f"[holders] FAILED: {hs['error']}")
        else:
            print(f"[holders] {hs['filers']} institutional holders across "
                  f"{hs['securities']} tracked securities from {hs['dataset']}"
                  + (f"; {hs['ct_releases']} confidential-treatment releases found"
                     if hs["ct_releases"] else ""))
            print(f"          scoped to the CUSIPs our funds hold; tail beyond the "
                  f"top 60 holders per security dropped ({hs['tail_dropped']} rows)")

    if do_crosscheck and not offline:
        c = fund_crosscheck.run(con, run_id)
        print(f"[xcheck]  13F vs DEF 14A — {c['match']} agree, "
              f"{c['discrepancy']} disagree (flagged, not resolved), "
              f"{c['unresolved']} unresolved")

    # ── audit gate ──────────────────────────────────────────────────────────
    verdict = fund_audit.run(con, run_id)
    print(f"[audit]   {'PASS' if verdict['passed'] else 'FAIL'} — "
          f"{len(verdict['errors'])} errors, {len(verdict['warnings'])} warnings "
          f"-> runs/{run_id}/fund_audit_report.md")
    for e in verdict["errors"][:15]:
        print("           ERR", e)
    for wn in verdict["warnings"][:10]:
        print("           WARN", wn)

    # ── payload ─────────────────────────────────────────────────────────────
    h = fund_handoff.run(con, run_id, audit_verdict=verdict)
    if not h["ok"]:
        print(f"[handoff] CONTRACT VIOLATED — file NOT written ({len(h['errors'])}):")
        for e in h["errors"][:20]:
            print("           ", e)
        return 1
    print(f"[handoff] {h['totals']['funds']} funds, {h['totals']['positions']} "
          f"positions, {h['totals']['events']} events -> {h['path']}")

    if deliver:
        if not verdict["passed"]:
            print("[deliver] BLOCKED: audit failed — fix the errors and re-run")
            return 1
        if not DELIVER_TO.parent.is_dir():
            print(f"[deliver] SKIPPED — no directory {DELIVER_TO.parent}")
        else:
            shutil.copy(h["path"], DELIVER_TO)
            print(f"[deliver] -> {DELIVER_TO}")
    con.close()
    return 0 if verdict["passed"] else 2


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rid = args[0] if args else date.today().isoformat()
    sys.exit(main(
        rid,
        backfill="--backfill" in sys.argv,
        offline="--offline" in sys.argv,
        do_adv="--adv" in sys.argv or "--backfill" in sys.argv,
        do_crosscheck="--crosscheck" in sys.argv,
        do_cap_tables="--cap-tables" in sys.argv or "--backfill" in sys.argv,
        deliver="--deliver" in sys.argv,
        reparse="--reparse" in sys.argv,
        do_holders="--holders" in sys.argv))
