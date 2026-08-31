# Audit report — 2026-W36 (2026-08-31)

**Verdict: FAIL — delivery blocked**
Checked 271 events, 115 track-record rows, 43 profiles, 165 target references, 351 holdings, 0 classified targets.

## Errors (21)
- E6 Amazon: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 American Electric Power: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 Arrive Logistics: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 Brookfield Middle East Partners: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 CMS Energy: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 DOE Genesis Mission (SPARK): target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 DTE Energy: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 DigitalBridge Group: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 Dili: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 DuckLabs: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 FirstEnergy: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 IREN Limited: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 Machine Age Fund: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 NAVER GAK Sejong AI Factory (South Korea): target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 PLUS ES: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 SB Energy: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 SB Energy PORTS-Pike Technology Campus (Ohio): target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 SK Horizon: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 Vista Energy: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 Vistra: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering
- E6 X-Energy: target on the map with no description — run tools/make_reference_batches.py + the target-profiler pass BEFORE delivering

## Warnings (46)
- W3 Apollo: key allocator with events but no profile
- W3 Elon Musk: key allocator with events but no profile
- W3 Goldman Sachs: key allocator with events but no profile
- W3 Max Levchin: key allocator with events but no profile
- W3 Palmer Luckey: key allocator with events but no profile
- W6 SB Energy PORTS-Pike Technology Campus (Ohio): $105.0B target with no reference
- W6 NAVER GAK Sejong AI Factory (South Korea): $9.0B target with no reference
- W6 DigitalBridge Group: $4.0B target with no reference
- W6 IREN Limited: $2.4B target with no reference
- W6 SB Energy: $1.5B target with no reference
- W6 Machine Age Fund: $1.1B target with no reference
- W7 MGX Fund I: $49.0B fund/firm with no holdings collected
- W7 BlackRock: $44.9B fund/firm with no holdings collected
- W7 KKR: $24.7B fund/firm with no holdings collected
- W7 KKR Global Infrastructure Investors V: $19.2B fund/firm with no holdings collected
- W7 SoftBank: $15.9B fund/firm with no holdings collected
- W7 Brookfield Infrastructure Fund VI (flagship): $7.9B fund/firm with no holdings collected
- W7 Thrive Capital: $6.6B fund/firm with no holdings collected
- W7 Azora: $5.0B fund/firm with no holdings collected
- W7 Brookfield AI Infrastructure strategy: $5.0B fund/firm with no holdings collected
- W7 Mubadala Capital (credit platform): $4.7B fund/firm with no holdings collected
- W7 Sequoia: $2.8B fund/firm with no holdings collected
- W7 Blue Owl: $2.4B fund/firm with no holdings collected
- W7 Machine Age Fund: $1.1B fund/firm with no holdings collected
- W9 Apollo: 15 of 190 holdings shipped — under the 25 floor; renders as 'top 15 of 190'
- W9 Blackstone: 14 of 53 holdings shipped — under the 25 floor; renders as 'top 14 of 53'
- W9 Brookfield: 20 of 60 holdings shipped — under the 25 floor; renders as 'top 20 of 60'
- W9 Coatue: 16 of 250 holdings shipped — under the 25 floor; renders as 'top 16 of 250'
- W8 MGX Fund I: $49.0B investable target with no ai_posture
- W8 SpaceX: $36.4B investable target with no ai_posture
- W8 Electronic Arts: $33.6B investable target with no ai_posture
- W8 OpenAI Group PBC: $21.3B investable target with no ai_posture
- W8 Databricks: $15.0B investable target with no ai_posture
- W8 OpenAI: $10.0B investable target with no ai_posture
- W8 Anthropic: $10.0B investable target with no ai_posture
- W8 Safe Superintelligence: $5.0B investable target with no ai_posture
- W8 Mubadala Capital (credit platform): $4.7B investable target with no ai_posture
- W8 Hadrian: $4.1B investable target with no ai_posture
- W8 Microsoft Frontier Company: $2.5B investable target with no ai_posture
- W8 IREN Limited: $2.4B investable target with no ai_posture
- W8 Thrive Holdings: $2.0B investable target with no ai_posture
- W8 Blue Origin: $2.0B investable target with no ai_posture
- W8 Atoms: $1.7B investable target with no ai_posture
- W8 Sila Nanotechnologies: $1.4B investable target with no ai_posture
- W8 Machine Age Fund: $1.1B investable target with no ai_posture
- W8 Poolside: $1.0B investable target with no ai_posture

## Stats
```json
{
  "events": 271,
  "by_status": {
    "candidate": 51,
    "verified": 173,
    "verified_alpha": 47
  },
  "source_url_coverage": 1.0,
  "estimated_amounts": 58,
  "provisional_track_rows": 42
}
```
