# Prompt for the ab-investment session — swap the "gaming" sector for "cybersecurity"

Paste into a Claude Code session in `ab-investment`. The engine retired the
`gaming` sector and added `cybersecurity`. The payload already reflects it; the
dashboard just needs its sector label / color / zone maps updated.

## What changed in the payload (`capital_map.json`)
- New sector key **`cybersecurity`** (holds Neo Security + Cathedral). Its default
  theme is **`cyber_security`**.
- **`gaming` no longer exists.** The one deal that was there (Saudi PIF →
  Electronic Arts) is now under **`diversified-pe`** (it's a PE take-private).

## What to change in the dashboard
In `src/data/capitalMap.js` (the META / palette maps) and anywhere sectors are
enumerated for the map zones, legend, and filters:
1. **Remove** the `gaming` entry (label, color, zone, RU translation «Игры»).
2. **Add** `cybersecurity`:
   - RU label: «Кибербезопасность» (keep your existing label style/casing).
   - Give it a color distinct from `defense-tech` (they're adjacent — don't reuse
     the defense hue). A cool cyan/teal or violet reads well as "security".
   - Add its map zone alongside defense-tech / ai-applications.
3. If you map themes, add **`cyber_security`** to the theme label/color set.
4. Nothing else: the EA node now simply appears in the `diversified-pe` zone — no
   special handling; confirm it renders there and not as an orphan.

## Verify
- A `cybersecurity` zone appears with Neo Security + Cathedral; no empty/gaming
  zone remains.
- Electronic Arts renders under `diversified-pe`.
- No sector shows as "unknown"/uncolored (a missing palette entry falls back to
  grey — if you see grey, a sector key is unmapped).
