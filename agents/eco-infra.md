# eco-infra — L10

**Read `agents/eco-CONTEXT.md` first.** Then the `L10` block of `config/eco_layers.yaml`.

You own the convergence layer: where chips, power and cooling become rentable compute.
Clouds, neoclouds, and datacenter REITs all sit here — the taxonomy is explicit about it,
so do not invent a layer for any of them.

## Who you track
- **Hyperscalers** — Microsoft (Azure), Alphabet (Google Cloud), Amazon (AWS), Oracle (OCI),
  Meta (own fleet).
- **Neoclouds** — CoreWeave, Crusoe, Nebius, Lambda, Fluidstack, Together.
- **DC REITs and developers** — Equinix, Digital Realty, Vantage, QTS, Compass, Aligned,
  Switch, Data4.

## What to look for — concretely
- **Capacity contracts with a named counterparty and a dollar value or a term.** These are
  `offtake` edges and they are the backbone of L10. Both sides usually announce → two
  evidence rows.
- **Revenue concentration in a neocloud's filing.** An S-1 or 10-K stating that a small
  number of customers are most of revenue is the single strongest `strength` evidence you
  can get, and it points the edge correctly (the *customer* is the dependency for the
  neocloud, and the *capacity* is the dependency for the customer — write the one the quote
  actually supports).
- **GPU purchase commitments** — a neocloud's disclosed purchase obligations to a named
  supplier are a `supply` edge from the chip vendor, with real numbers.
- **Vendor financing and equity in customers.** When a supplier also holds a stake in its
  customer, that is a `stake` edge on the capital spine AND a `supply` edge on the physical
  one. Write both; they are what makes a cycle detectable.
- **Leases and build-to-suit deals** between a REIT/developer and a hyperscaler.
- **Own-silicon programs** (Trainium, TPU, Maia, Axion) — these make a hyperscaler an L3
  node too. One node, several layers.

## Mandatory tier-1 checks per anchor
- Microsoft, Alphabet, Amazon, Oracle: latest 10-K, the most recent 10-Q, and the earnings
  call transcript — RPO/backlog commentary on the call is where the offtake shows up first.
- CoreWeave, Nebius: 10-K / 20-F / S-1 and the IR newsroom. These filings are unusually
  explicit about customer concentration; read them properly.
- Equinix, Digital Realty: 10-K plus the quarterly supplemental.

## Layer gotchas
- **A hyperscaler is both `demand` and `owner`.** Pick the role by what dominates its
  presence on the map (usually `demand` for the labs' suppliers, `owner` for its own
  fleet), keep it consistent, and let the *edges* carry the nuance.
- **A neocloud is a customer of NVIDIA and a supplier to a lab at the same time.** That is
  exactly the shape that closes a cycle — get both edges, with sources, or the cycle lens
  has nothing to find.
- **Do not double-count a company that also builds chips.** Amazon designing Trainium is an
  L3 row on the Amazon node, not a second "AWS Silicon" node.
- Announced *investment intentions* ("we will invest $X billion in region Y") are not
  edges. A named counterparty is required.
