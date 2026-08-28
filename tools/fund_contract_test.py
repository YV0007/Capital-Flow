"""Proves the Fund Tracker's handoff contract still bites.

Same job as tools/nveco_corrupt_test.py: a validator nobody tests is a validator
that quietly stopped working. Each case below corrupts a valid payload in exactly
one way and asserts the writer refuses it — because handing the dashboard a broken
file is worse than handing it nothing. A missing update is visibly missing; a
corrupt one lies quietly.

    python tools/fund_contract_test.py
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import fund_handoff                                    # noqa: E402


def _base() -> dict:
    """A minimal payload that must PASS. Anything failing here is a real bug."""
    return {
        "contractVersion": "1.0", "generated": "2026-08-23T00:00:00Z",
        "section": "fund-tracker",
        "funds": [{
            "fund": "duquesne", "name": "Duquesne Family Office LLC",
            "styleTag": "concentrated", "convictionWeight": 1.0,
            "managerClass": "sparse_coverage",
            "whyTracked": "Small, concentrated, closely watched.",
            "focus": "Global macro expressed in equities.",
            "primarySource": "13F-HR",
            "book": {"period": "2026-06-30", "latencyDays": 45, "staleness": "stale",
                     "holdings": [{"issuer": "NATERA INC", "instrument": "common",
                                   "shares": 3186306, "valueUsd": 864923000,
                                   "weight": 0.199,
                                   "sourceUrl": "https://sec.gov/x"}],
                     "derivatives": []},
            "deltas": {"added": [{"issuer": "NATERA INC", "instrument": "common",
                                  "shareDeltaPct": 0.04, "pctChangeSuppressed": False}],
                       "hedges": []},
        }],
        "crowding": [], "watchOnly": {"funds": [], "triggers": []},
        "coverageGaps": [],
        "timeline": [{"headline": "added to NTRA", "latencyDays": 45,
                      "staleness": "stale", "sourceUrl": "https://sec.gov/x"}],
        "totals": {"funds": 1},
    }


CASES = [
    ("a fund with no styleTag",
     lambda p: p["funds"][0].pop("styleTag")),
    ("a fund with no whyTracked (the identity card would render blank)",
     lambda p: p["funds"][0].update(whyTracked="")),
    ("a holding with no source URL",
     lambda p: p["funds"][0]["book"]["holdings"][0].pop("sourceUrl")),
    ("a timeline event with no latencyDays (a stale position read as fresh)",
     lambda p: p["timeline"][0].pop("latencyDays")),
    ("a timeline event with no staleness label",
     lambda p: p["timeline"][0].pop("staleness")),
    ("a timeline event with no source URL",
     lambda p: p["timeline"][0].update(sourceUrl=None)),
    ("a book with no latencyDays",
     lambda p: p["funds"][0]["book"].pop("latencyDays")),
    ("a PUT sitting in a long-conviction feed",
     lambda p: p["funds"][0]["deltas"]["added"][0].update(instrument="put")),
    ("a % change emitted below the materiality gate",
     lambda p: p["funds"][0]["deltas"]["added"][0].update(pctChangeSuppressed=True)),
    ("a watch-only manager carrying a standing book",
     lambda p: p["funds"][0].update(managerClass="watch_only")),
    ("two funds sharing one id",
     lambda p: p["funds"].append(copy.deepcopy(p["funds"][0]))),
    ("coverage gaps dropped (completeness implied where there is none)",
     lambda p: p.update(coverageGaps=None)),
    ("a snake_case key in the payload",
     lambda p: p.update(fund_count=1)),
    # Task C-2: holdings[] answers "what does this fund own right now".
    ("a PUT inside holdings[] (states the opposite of the truth, and its notional "
     "inflates every weight around it)",
     lambda p: p["funds"][0]["book"]["holdings"][0].update(instrument="put")),
    ("a CALL inside holdings[] (notional, not ownership)",
     lambda p: p["funds"][0]["book"]["holdings"][0].update(instrument="call")),
    ("a WARRANT inside holdings[]",
     lambda p: p["funds"][0]["book"]["holdings"][0].update(instrument="warrant")),
    ("a bond reported as PRN inside holdings[]",
     lambda p: p["funds"][0]["book"]["holdings"][0].update(instrument="prn")),
    ("an EXITED zero-share row inside holdings[]",
     lambda p: p["funds"][0]["book"]["holdings"][0].update(shares=0)),
]


def main() -> int:
    ok = fund_handoff.validate(_base())
    if ok:
        print("FAIL: the clean payload was rejected — the validator is too strict")
        for e in ok:
            print("   ", e)
        return 1
    print("clean payload accepted ✓\n")

    failures = 0
    for name, corrupt in CASES:
        p = _base()
        corrupt(p)
        errs = fund_handoff.validate(p)
        if errs:
            print(f"  caught: {name}\n          -> {errs[0]}")
        else:
            print(f"  MISSED: {name}")
            failures += 1
    print()
    if failures:
        print(f"FAIL — {failures} of {len(CASES)} corruptions slipped through")
        return 1
    print(f"PASS — all {len(CASES)} corruptions rejected; the contract still bites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
