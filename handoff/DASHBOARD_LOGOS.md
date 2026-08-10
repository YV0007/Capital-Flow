# Prompt for the ab-investment session — fix logo coverage

Paste into a Claude Code session in `ab-investment`. Three fixes; ~47 monogram
tiles become real logos, and 7 that already have a downloaded file start showing it.

## Background — why so many monograms
`scripts/fetch_logos.py` resolves each entity's domain from `entityReference.json`
or, failing that, **guesses the domain from the entity name**. Guessing fails for
the exact things that are monograms: data-center campuses, fund vehicles, SPVs
(e.g. "Richland Parish / Hyperion data center", "MGX Fund I"). The engine already
researched these entities' official sites and **now emits a clean `domain` on the
node itself** in `capitalMap.json` (86 of 166 nodes, incl. 36 current monograms).
The script just isn't reading it.

## Fix 1 — make the fetcher prefer the node's own domain/links (the big one)
In `scripts/fetch_logos.py`, `entities()` pulls links only from
`entityReference.json` (`meta.get("links")`). Change it to prefer what the node
carries:
- Use `n.get("domain")` as the FIRST domain candidate when present (it's the
  engine's researched, authoritative site).
- Merge `n.get("links")` with the reference's links (node links win), mirroring
  what the app already does at `capitalMap.js:463`.

Then in the resolution block, try the node `domain` before `guess_domains(name)`.
Keep the existing `page_is()` verification — an authoritative domain still gets
verified, so a wrong emit can't sneak a bad logo in.

## Fix 2 — resync the manifest with files already on disk
`public/logos/` has 7 images with no `logoManifest.json` entry, so they render as
monograms despite existing (`Firmus`, `Lancium`, `Discovery Loop`,
`Mariana Minerals`, `Whatnot`, `Niron Magnetics`, `Prime Intellect`). A full
`python scripts/fetch_logos.py` run (not `--only-missing`) rewrites the manifest
from disk and picks up the new node domains. Run it and commit the manifest +
any new `public/logos/*`.

## Fix 3 — wire the runtime fallback (or delete it)
`buildLogoUrls(links)` in `capitalMap.js` (≈399-422) derives favicon/unavatar URLs
from links but is **never called** — dead code. Either call it in `buildGraph` so a
node with a `domain`/`website` but no downloaded file still shows a favicon instead
of a monogram, or delete it. Calling it is the better fix: it gives an instant
fallback for any entity the batch fetch hasn't covered yet.

## After
Re-run `fetch_logos.py`, check `scripts/logo-misses.txt` shrinks from ~48 toward
the genuinely logo-less (unnamed SPVs, government campuses — a monogram there is
correct). The engine's weekly delivery already invokes this script, so once Fix 1
lands, each cycle's new entities resolve automatically from their emitted domain.

## Note back to the engine if
Any monogram remains for an entity that clearly has a real site — that means the
engine didn't emit a `domain` for it (no reference website yet). Tell the engine
side which entity; it's a reference-coverage gap, not a dashboard bug.
