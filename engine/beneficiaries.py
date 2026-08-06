"""Beneficiary engine: map private capital flows to public-market beneficiaries.

For each new verified event (and each fired theme), determine which public
companies benefit — suppliers, picks-and-shovels, direct competitors losing,
platform owners — and write rows to the beneficiaries table with a rationale
and confidence. This step is agent-assisted (reasoning), but its output is
stored deterministically in the DB.
"""


def run(week: str) -> None:
    raise NotImplementedError("Build step 7: beneficiary engine")
