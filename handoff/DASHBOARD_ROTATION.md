# Prompt for the ab-investment session — time-window rotation + Monday promotion pop-up

Paste into a Claude Code session in `ab-investment`. Two features, both fed by the
engine payload; the dashboard owns the UI, the engine owns the facts and the rules.

## Feature 1 — default view is a trailing time window (deterministic)

The map must not show all history at once. Filter flows by recency; nothing is
deleted, only hidden — the user widens the window to see more.

Payload gives you, per `flows[]`:
- `age_days` — days since the flow's date.
- `active_signal` — `true` if the flow is part of a signal fired this cycle.

And a top-level `view_defaults`: `{default_window_days: 30, windows: [7,30,90,null], keep_active_signal: true}`.

**Inclusion rule (pure, no judgment):** show a flow if
`age_days <= window` **OR** (`keep_active_signal` and `active_signal`).
The second clause is the keep-alive — a pivotal older flow tied to a live signal
stays in view by rule, not opinion.

**UI:** a window toggle `1w / 30d / 90d / All`, defaulting to `view_defaults.default_window_days`.
`null` = all-time (no age filter). A node with no visible flows drops out of the
view for that window (it isn't deleted — it returns when the window widens).
Keep the existing emphasis (confidence / signal strength / capital) for what's
*shown* — this only controls what's *in view*.

## Feature 2 — the Monday promotion pop-up (human-decided)

The engine discovers co-investors but NEVER auto-adds them. Each delivery ships
`promotion_queue[]`: candidates awaiting the user's decision. Each item:
`{candidate_id, name, suggested_class, seen_with[], description, times_seen, first_seen}`.

**UI:** once a week (gate on a "last reviewed week" key in localStorage, tied to the
payload's `generated` date so it shows once per new delivery), open a pop-up listing
the queue — ranked by `times_seen` desc. Each row: name, suggested class, the
`description` (quick why-track-them), `seen_with` chips, and a **Yes / No** toggle.
A "Review later" closes it without deciding (it reappears next week).

**Applying the decision (the one cross-repo hop):** the dashboard is static, so it
can't write the engine's config. On submit, collect the picks and produce a small
decisions block the engine consumes:
```json
{ "promote": [ {"name": "Lightspeed", "class": "vc", "tier": "watch"} ],
  "dismiss": [ "Some Name" ] }
```
Persist it to localStorage AND offer it as **copy-to-clipboard / download**
(`decisions.json`). The user hands it to the engine's Monday run, which applies it:
`python tools/promote.py --from decisions.json`. Promoted names are tracked from the
next run and appear on the map; dismissed ones leave the queue. (If you later add any
persistence/backend, write `decisions.json` directly — the engine command is unchanged.)

Do NOT promote or hide anything on the dashboard side — you render the queue and
capture the choice; the engine owns who is tracked.

## Verify
- Default map shows ~30 days of flows; toggling to All reveals the full history;
  an older flow with `active_signal:true` stays visible at 30d.
- The pop-up appears once for a new delivery, lists candidates ranked by frequency,
  and exports a clean `decisions.json` on submit.
