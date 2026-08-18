# eco-models — L11–L12

**Read `agents/eco-CONTEXT.md` first.** Then the `L11`, `L12` blocks of
`config/eco_layers.yaml`.

You own the demand end: what runs the models, and who pays for the answer. Everything the
rest of the map builds exists to serve this layer — which makes your edges the ones that
prove the stack is load-bearing rather than speculative.

## Who you track
- **L11 ИНФЕРЕНС** — serving and orchestration: Databricks, Hugging Face, Together AI,
  Fireworks, Baseten, Groq and Cerebras where they sell inference rather than silicon.
- **L12 РЕЗУЛЬТАТ** — frontier labs (OpenAI, Anthropic, Google DeepMind, Meta AI, xAI,
  Mistral, SSI) and the AI-for-business layer that turns model output into revenue.

## What to look for — concretely
- **Compute commitments from a lab to a named provider.** Term, dollar value, megawatts —
  quote whichever the release states. These are `offtake` edges and they are the most
  consequential lines on the map.
- **Exclusivity and right-of-first-refusal language** in partnership announcements — it is
  the difference between `offtake` at strength 90 and at strength 40.
- **Model-availability agreements** — a lab's models offered on a named cloud is a
  `platform` edge from the lab into that cloud's product.
- **Investment from a supplier into a lab.** A chip vendor or a cloud taking a stake in a
  lab it also sells to is a `stake` edge that closes a sales loop. Get the ownership
  language from a filing where one exists.
- **Enterprise deployments with a named customer** — this is what makes L12 more than a
  list of labs, but it needs a named counterparty, not a case-study page.
- **Inference pricing and capacity statements** on earnings calls — `transcript` tier,
  useful for `share_note`.

## Mandatory tier-1 checks per anchor
- OpenAI and Anthropic are **private**: the citable documents are their own announcement
  pages, the counterparty's press release, and the counterparty's filings. A hyperscaler's
  10-K/10-Q often describes the lab relationship in more detail than the lab does.
- Microsoft, Alphabet, Amazon, Meta: the AI-commitment language in the latest 10-K/10-Q and
  on the earnings call.
- Databricks and Hugging Face are private — use funding announcements and partner PRs, and
  mark the tier honestly.

## Layer gotchas
- **A lab is `demand`, not `producer`.** It consumes the stack. Its criticality comes from
  being irreplaceable to *its* customers, which for most labs today is genuinely modest —
  score it honestly. A frontier lab with real substitutes is a 2–3 on `f_alternatives`, not
  a 5.
- **Inference ≠ frontier lab.** Serving someone else's model is L11; training your own is
  L12. Companies doing both get two layer rows on one node.
- **Beware the announcement treadmill.** This layer produces more press than any other and
  less documentation. If the only source is a blog post with no counterparty confirmation,
  it is `company_pr` at best, single-source, dashed — and that is fine. Do not upgrade a
  tier to make a line look better.
- Do not write an edge from a lab to "the industry". Named counterparties only.
