# Beneficiary Mapper (post-research pass)

Not one of the six research agents — this runs AFTER events are ingested and
themes fired. It maps private/large capital flows to **public-market beneficiaries**
(the "who benefits" layer of the platform).

**Read `agents/CONTEXT.md` first.** Then read `runs/<week>/weekly_report.md` and the
verified events for the week (query the DB or read the CSVs).

## What you do
For each material verified event (and each fired theme), name the public companies
that benefit — suppliers, picks-and-shovels, platform owners, capacity providers —
and why. Prefer names already in the ecosystem (fab-equipment, power, silicon).

## Output — `runs/<week>/beneficiaries.csv`, this exact header:
```
allocator,target,event_type,disclosed_date,ticker,company,rationale,confidence
```
- The first four columns identify the source event (must match an ingested event
  exactly, so the engine can link it).
- `ticker` public symbol, `company` name, `rationale` one line on the linkage,
  `confidence` low|medium|high.

## Discipline
- Only public, tradeable beneficiaries. No private targets.
- One row per (event, beneficiary). A single flow can have several beneficiaries.
- Be conservative on `confidence` — a direct supplier is `high`; a thematic
  second-order read is `low`.
