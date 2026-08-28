"""Launching the holdings-profiler agents — the step that never ran.

`tools/make_holdings_batches.py` has always written correct batch inputs, and
`engine/holdings.py` has always ingested correct results. Between them sat a line
in RUNBOOK.md addressed to a person: *"launch one holdings-profiler agent per
batch"*. Nothing launched them. In W33 four batches were written and zero agents
ran; in W34, three of four. Those three batches are the entire origin of every
portfolio on the site, and the reason thirty-six funds render empty.

This module closes that gap. It resolves a launcher, runs one agent per batch in
parallel, and waits.

**On not having a launcher.** The launcher is a real external program, and if this
machine has none, the honest outcome is a LOUD failure — not a run that prints
"0 portfolios" and ships green, which is precisely the failure mode being fixed.
`resolve()` returning None is a hard stop with the remediation printed, never a
silent skip.

Resolution order:
  1. `$HOLDINGS_AGENT_CMD` — a shell template. Placeholders: {batch_dir},
     {prompt_file}, {brief}, {period}, {batch}. This is the escape hatch for any
     runner: a different CLI, a queue, an HTTP call to a hosted agent.
  2. the `claude` CLI on PATH, in headless `-p` mode.
  3. nothing — fail loudly.
"""

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from . import db

BRIEF = db.ROOT / "agents" / "holdings-profiler.md"
CONTEXT = db.ROOT / "agents" / "CONTEXT.md"
DEFAULT_TIMEOUT = int(os.environ.get("HOLDINGS_AGENT_TIMEOUT", "3600"))

PROMPT = """You are the **holdings-profiler** research agent for the Capital Flow engine.

Working directory: {root}

1. Read `agents/CONTEXT.md` (source-tier ladder), then `agents/holdings-profiler.md`
   (your full brief and output contract), then `config/rules.yaml` (the canonical
   sector / subsector vocabulary you must use).
2. Your batch input is `{batch_dir}/batch_entities.json`. Research EVERY entity in it.
3. Write `{batch_dir}/holdings.json` — a JSON array, one object per entity, in
   exactly the shape the brief specifies.

Non-negotiable, because the ingest enforces them and will drop what fails:
- Every holding needs its own real `source_url`. No source, no holding.
- Ship **at least {minimum}** holdings per entity where the portfolio supports it.
  Each entity's `instruction` field tells you what it already has and what it must
  beat; an entity marked `"reason": "thin"` needs a DEEPER list, not a re-send.
- `holdings_count` is the entity's TRUE total, even when the array is a subset.
- `portfolio_url` must be the portfolio LISTING page, never the marketing homepage.
- For a portfolio too large to enumerate, rank by relevance to this map first —
  the sectors in each entity's `rank_by` field — then by stake size and notability.
- Sectors must come from `config/rules.yaml`. Keep a holding's `name` byte-identical
  to a map node label where the company is itself tracked — a near-miss name
  silently breaks the dashboard's link through to that node.
- A HOLDING is an equity stake the fund STILL OWNS. Exclude realised exits (sold
  after an IPO or acquisition), LP commitments into other funds, debt and
  venture-debt, announced-but-unclosed deals, and pass-through SPV participation.
  A stake held through an IPO is still a holding; an undisclosed size is still a
  holding (`stake: null`).

Public sources only: the fund's own portfolio page, its press releases, SEC EDGAR
(ADV / Form D / 13F). Facts only — no estimates, no inference, no fabrication.
"""


class NoLauncher(RuntimeError):
    """No way to launch an agent on this machine. A hard stop, never a skip."""


def resolve() -> dict:
    cmd = os.environ.get("HOLDINGS_AGENT_CMD")
    if cmd:
        return {"kind": "env", "template": cmd}
    exe = shutil.which("claude")
    if exe:
        return {"kind": "cli", "exe": exe}
    return None


def remediation() -> str:
    return (
        "No agent launcher available, so the collection step CANNOT run.\n"
        "  This is the one step that has never been automated, and it is why 36\n"
        "  funds render empty. Failing loudly rather than shipping an empty run.\n\n"
        "  Fix it either way:\n"
        "    1. install the Claude Code CLI so `claude` is on PATH, or\n"
        "    2. export HOLDINGS_AGENT_CMD with your own runner, e.g.\n"
        '       export HOLDINGS_AGENT_CMD=\'claude -p "$(cat {prompt_file})\' \n'
        "       placeholders: {batch_dir} {prompt_file} {brief} {period} {batch}\n\n"
        "  Until then, agents can be launched by hand from a Claude Code session\n"
        "  (one per batch, prompt written to <batch_dir>/prompt.txt) and\n"
        "  `python run_holdings.py <period> --no-agents` will ingest the results."
    )


def write_prompt(batch_dir: Path, period: str, minimum: int = 25) -> Path:
    """Materialise the agent prompt beside its input.

    On disk on purpose: it is the audit trail of what was actually asked, it is
    what a hand-launched agent can be pointed at, and it is what a custom
    HOLDINGS_AGENT_CMD interpolates.
    """
    text = PROMPT.format(root=db.ROOT, batch_dir=batch_dir, minimum=minimum)
    path = batch_dir / "prompt.txt"
    path.write_text(text)
    return path


def _command(launcher: dict, batch_dir: Path, prompt_file: Path, period: str) -> list:
    fields = {"batch_dir": str(batch_dir), "prompt_file": str(prompt_file),
              "brief": str(BRIEF), "period": period, "batch": batch_dir.name}
    if launcher["kind"] == "env":
        return ["/bin/sh", "-c", launcher["template"].format(**fields)]
    return [launcher["exe"], "-p", prompt_file.read_text(),
            "--permission-mode", "acceptEdits"]


def launch(batch_dirs, period: str, minimum: int = 25,
           timeout: int = DEFAULT_TIMEOUT, launcher: dict = None) -> dict:
    """Run one agent per batch, in parallel, and wait for all of them."""
    launcher = launcher or resolve()
    if not launcher:
        raise NoLauncher(remediation())

    procs, stats = [], {"launched": 0, "ok": 0, "failed": [], "timed_out": [],
                        "kind": launcher["kind"]}
    for bd in batch_dirs:
        prompt_file = write_prompt(bd, period, minimum)
        cmd = _command(launcher, bd, prompt_file, period)
        log = open(bd / "agent.log", "wb")
        procs.append((bd, subprocess.Popen(cmd, cwd=str(db.ROOT), stdout=log,
                                           stderr=subprocess.STDOUT), log))
        stats["launched"] += 1

    deadline = time.monotonic() + timeout
    for bd, proc, log in procs:
        try:
            rc = proc.wait(timeout=max(1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            proc.kill()
            stats["timed_out"].append(bd.name)
            rc = -1
        finally:
            log.close()
        # The real test is not the exit code, it is whether the file exists. An
        # agent can exit 0 having written nothing, and that is still a failure.
        if rc == 0 and (bd / "holdings.json").exists():
            stats["ok"] += 1
        else:
            stats["failed"].append(
                f"{bd.name} (rc={rc}, holdings.json "
                f"{'present' if (bd / 'holdings.json').exists() else 'MISSING'})")
    return stats


def pending_batches(period: str) -> list:
    """Batch dirs with an input and no result — the work still to do."""
    hdir = db.RUNS_DIR / period / "holdings"
    if not hdir.is_dir():
        return []
    return [d for d in sorted(hdir.iterdir())
            if d.is_dir() and (d / "batch_entities.json").exists()
            and not (d / "holdings.json").exists()]
