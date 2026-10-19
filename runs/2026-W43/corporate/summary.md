# Corporate Class -- Weekly Summary (2026-W43)

## What moved this week
The corporate/hyperscaler watchlist (Microsoft, Amazon, Alphabet, Meta, Oracle, NVIDIA) produced one clear cluster: **NVIDIA went on a minority-stake spree in Paris**, plus two large compute/research commitments, while **Meta quietly expanded a compute-capacity deal with Firmus Technologies** in Southeast Asia. Microsoft, Amazon, Alphabet and Oracle produced no new disclosed balance-sheet or CVC capital-allocation events into the canonical sectors in the last ~30 days beyond what is already on file (Anthropic/OpenAI stakes, the Alphabet $80B+ equity raise, Oracle's $45-50B 2026 funding plan) -- those are capex/financing stories, not new allocations into a target, so they were not re-filed.

## 2-3 biggest signals
1. **NVIDIA's European minority-stake push (Oct 13, Paris).** Jensen Huang announced undisclosed minority stakes in four French companies in one sweep: Doctolib (healthtech), Pigment (FP&A software), Genesis AI (robot foundation models) and Entalpic (AI-for-materials-science). None of the amounts were disclosed by Nvidia or the targets -- this is relationship/ecosystem buying, not scale. Huang separately said Nvidia expects to announce ~$2B more in European investment within the week; that is forward guidance only and is filed as a single candidate row with no target yet.
2. **NVIDIA is now funding the research base, not just products.** Two back-to-back commitments -- $1B over 5 years to US university/quantum-computing/Genesis Mission research (Oct 8, DC) and $250M of UK compute over 5 years for agentic-AI-safety research at Oxford/UCL/Imperial (Oct 13-14) -- are real committed capital but structurally different from equity: one is a grant to research infrastructure, the other is compute-in-kind, not cash. Both are flagged in notes as atypical for the amount_usd convention and mapped to the closest canonical sector/theme rather than a perfect match.
3. **Meta-Firmus (Sept 29-30) is a compute commitment with the economics withheld.** Meta extended its Nvidia-chip compute relationship with Firmus from Melbourne into new Southeast Asia sites -- real, corroborated by Reuters-relayed wires and Firmus's own statement, but neither side disclosed a dollar figure. Filed as verified (the deal itself is solid) with amount_usd blank per the no-guessing rule.

## What did NOT make the cut
- NVIDIA/Figure AI ($1B "in talks" per The Information, Oct 7) was already on file from W42 as candidate; no new corroboration this week, so it was not re-filed (avoiding churn).
- NVIDIA/Hugging Face ($12.93B acquisition) and Alphabet(GV)/Snorkel AI ($350M follow-on) are already verified on file from prior weeks; confirmed via `engine.edgar exists` and left untouched.
- Amazon's reported ~$8B Nvidia-chip SPV (FT/Benzinga, Oct 2) was excluded: in that structure outside investors are the allocators and Amazon is raising financing/leasing chips back -- Amazon is not deploying capital as the allocator, so it is out of scope for this class.
- Oracle, Microsoft and Alphabet's big 2026 figures (capex guidance, the $80B+ equity raise, the $45-50B funding plan) are the companies spending/raising on their OWN infrastructure, not allocating capital into a third-party target -- not events under this engine's definition.

## What to watch next week
- Whether NVIDIA's teased ~$2B of further European investment lands, and against which named targets (would upgrade the W43 candidate row).
- Whether the Figure AI $1B follow-on (still "in talks" as of Oct 7) gets confirmed or denied.
- EDGAR deterministic tool (`engine.edgar filings`) was blocked by the sandbox network proxy (403 on the outbound SEC tunnel) for all six watchlist names this run -- 8-K/13D sweeps for NVIDIA, Meta, Alphabet, Amazon, Microsoft and Oracle could not be run directly and relied on secondary reporting instead. Worth fixing proxy access for the EDGAR CLI before next run so Tier-1 filing confirms are not skipped.
