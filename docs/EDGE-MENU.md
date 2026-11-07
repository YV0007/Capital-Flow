# EDGE MENU — what each connection would buy us

Mark each one KEEP / CUT. The argument line is the case for including it: what you would
see on the map that you cannot see without it. If that line does not convince you, cut it.

Grade: **A** = a filed document states it (free, repeats every quarter, change detection is automatic).
**B** = a number exists but from PR, press or a paid source. **C** = no number; judgment.

---

## 1. WHO MAKES WHOSE STUFF — physical dependency

**supplies_component** — A's part is inside B's product.
*Why:* the spine. Every "who is irreplaceable" question resolves into this one edge.
*Source:* 10-K concentration note · supplier lists · teardowns. *Number:* % of A's revenue. **A**

**manufactures_for** — A fabricates the chip B designed.
*Why:* separates who designs from who can physically build. TSMC's grip is invisible without it.
*Source:* 10-K · foundry disclosures. *Number:* wafer starts, % of capacity. **A/B**

**packages_assembles** — A does advanced packaging and test for B.
*Why:* packaging, not wafers, has been the real ceiling on accelerator output. Folded into "supplies" it disappears.
*Source:* OSAT filings · capacity commentary. *Number:* capacity units. **B**

**supplies_equipment** — A sells fab tools to B.
*Why:* the tool order book is the earliest read on capacity that will exist in 4–6 quarters. It leads chip revenue.
*Source:* ASML/AMAT/LRCX 10-K by customer and region. *Number:* $ bookings, tool count. **A**

**supplies_materials** — A sells wafers, resist, gases, substrates to B.
*Why:* tiny line items with monopoly suppliers. Low $, total shutdown risk — the asymmetry is the point.
*Source:* Shin-Etsu / JSR / Ibiden reports · SEMI. *Number:* share %, volume. **B**

**assembles_systems** — A builds B's servers and racks.
*Why:* shows where margin is thin versus fat, and Taiwan ODM monthly revenue is one of the fastest public reads on AI server demand anywhere.
*Source:* TWSE monthly revenue · Dell/HPE/SMCI 10-K. *Number:* units, $. **A**

**sole_source** — B has no qualified alternative to A.
*Why:* this single flag *is* the chokepoint detector, and companies are legally required to disclose it in risk factors.
*Source:* 10-K risk factors. *Number:* binary + the product named. **A**

**second_source** — B qualified an alternative to its main supplier.
*Why:* the counter-signal. The day a second source qualifies, the incumbent's pricing power has a date on it.
*Source:* qualification PR · earnings calls. *Number:* share split. **B**

---

## 2. WHO BOOKED WHOSE CAPACITY — committed demand

**capacity_reservation** — B prepaid or reserved A's future capacity.
*Why:* money committed before delivery is the hardest demand signal that exists. Everything else is intention.
*Source:* 8-K · contract-liabilities note · S-1. *Number:* $ prepaid, years. **A**

**provides_compute** — A sells B compute under a long-term contract.
*Why:* the largest contracts in the industry sit here, and they tie a lab to a cloud for years. Backlog is disclosed.
*Source:* 8-K · RPO/backlog disclosure · S-1. *Number:* $, years, MW. **A**

**leases_dc_space** — A leases data-centre space to B.
*Why:* where the compute physically lands. REITs disclose tenant, MW and term, so it is cheap to keep current.
*Source:* REIT leasing disclosures. *Number:* MW, $/yr, term. **A**

**power_purchase** — A supplies electricity to B's sites.
*Why:* power is the binding constraint now. A PPA is a dated, sized claim on the scarce input.
*Source:* utility filings · FERC · PPA announcements. *Number:* MW, years, $/MWh. **A/B**

**grid_queue** — B's site is waiting on interconnection.
*Why:* the earliest signal that exists for capacity 2–4 years out. Public, free, and almost nobody reads it.
*Source:* PJM / ERCOT / ISO queues · permits. *Number:* MW, energisation date. **A**

**builds_datacenter** — A develops or constructs B's site.
*Why:* county permits reveal a build before the press release does.
*Source:* permits · construction PR. *Number:* MW, $ capex. **B**

---

## 3. WHO PAYS FOR WHOM — money

**invests_equity** — A owns part of B.
*Why:* shows alignment, and crossed with supply edges it exposes circular financing — the supplier funding its own customer.
*Source:* 8-K · S-1 cap table · 13D/G · equity-method note. *Number:* $, % owned. **A**

**lends** — A extends credit to B.
*Why:* a chain financed by debt breaks differently from one financed by cash flow. This is the fragility axis.
*Source:* 8-K credit agreements · bond prospectus. *Number:* $, rate, maturity. **A**

**backstops** — A guarantees B's obligations or revenue.
*Why:* it names who actually eats the loss if demand disappoints. Guarantees are disclosed and almost never mapped.
*Source:* 10-K guarantees note · 8-K. *Number:* $ exposure. **A**

**equipment_finance** — A finances or leases B's hardware.
*Why:* GPU-backed debt is how the neocloud layer was built. Its terms decide who survives a price drop.
*Source:* ABS deals · lease disclosures. *Number:* $, term, collateral. **A**

**joint_venture** — A and B jointly own an entity.
*Why:* JVs are the largest single capital decisions in the industry, and they lock two parties together for a decade.
*Source:* JV agreements · 8-K. *Number:* $ committed, % each. **A**

**acquires** — A bought B or part of it.
*Why:* the industry restructures by M&A. Without this edge the map silently goes out of date.
*Source:* 8-K · merger filings. *Number:* $, date. **A**

**revenue_share** — B pays A a share of its revenue.
*Why:* the cleanest measure of how much value one node extracts per unit of everyone else's output (Arm is the type case).
*Source:* licence agreements · royalty revenue line. *Number:* rate %, $. **A**

---

## 4. WHO IS ALLOWED TO USE WHAT — rights and data

**licenses_chip_ip** — B builds on A's chip IP.
*Why:* an entire layer of control that moves no goods and appears nowhere else on the map.
*Source:* 10-K royalty revenue · licence PR. *Number:* royalty %, $. **A**

**licenses_eda** — B designs chips with A's tools.
*Why:* two companies gate every chip design on earth, and it is the sharpest export-control lever that exists.
*Source:* vendor revenue disclosures. *Number:* $, seats. **B**

**licenses_data** — A lets B train on its data.
*Why:* the only edge that shows who owns the training input and what it costs. Without it the Data chapter is empty.
*Source:* deal PR · publisher disclosures · S-1. *Number:* $/yr, term. **B**

**supplies_labeled_data** — A provides labelling or expert feedback to B.
*Why:* model quality is bought, not just trained. This shows who is paid for it and how much.
*Source:* customer disclosures · S-1 · PR. *Number:* $ contract. **B**

**model_api_access** — B's product is built on A's model.
*Why:* the demand side of the model layer — which apps would break if one lab changed its terms. S-1 risk factors state it plainly.
*Source:* S-1 dependency disclosures · PR. *Number:* $ spend, % of COGS. **B**

**distribution_deal** — A puts B's model in front of its users.
*Why:* distribution decides which model gets used at all. It is the biggest driver of lab revenue that is not capex.
*Source:* 10-K · PR. *Number:* users reached, $. **B**

---

## 5. WHO IS EXPOSED TO WHOM — control and risk

**export_license_dep** — A needs a government licence to sell to B.
*Why:* one rule change deletes a revenue line. This is the political axis, and it comes from a public register.
*Source:* BIS rules and entity list · 10-K risk factors. *Number:* % of revenue at risk. **A**

**rights_dispute** — A and B are in court over data or IP.
*Why:* a dated, sized claim on future cost that can invalidate a whole training pipeline.
*Source:* court dockets · 10-K legal proceedings. *Number:* claim $, filing date. **A**

**co_develops** — A and B run a joint engineering program.
*Why:* custom-silicon programs are how a buyer escapes its supplier. Usually the first visible sign of a future rupture.
*Source:* joint PR · program announcements. *Number:* $ committed. **B**

---

## 6. NOT WORTH AN EDGE — my argument for cutting

- **competes_with** — true of everyone in a segment; carries no number. → node attribute, from 10-K Item 1.
- **substitute_for** — matters for moat erosion, but adoption data is rarely public. → node attribute with evidence.
- **board_seat** — real control, but it is a property of an investment. → flag on `invests_equity`.
- **standard_adoption / benchmark_position** — no money moves. → node attributes.
- **hosts_model** — availability on a platform is not a commitment.
- **talent_flow** — scraped, unverifiable, and noisy.
- **patent_cross_license** — rarely material at this layer and expensive to source.
- **validates_demand / proves_roi / path_dependent_on / optimizes_for / enables** — the current map's judgment layer. No document, no number.

---

## If you want the lean version

Eight edges cover roughly 80% of the value and are all grade A:

`supplies_component` · `manufactures_for` · `supplies_equipment` · `sole_source` ·
`provides_compute` · `invests_equity` · `lends` (money-in, all forms) · `licenses_data`

Everything else can be added later without restructuring anything, because each edge type is
independent: it has its own source, its own unit and its own refresh cadence.
