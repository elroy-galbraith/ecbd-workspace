# How to audit

Method for `02-audit/`. Loaded by every audit stage that answers questions — the rules apply where the answers are written, not only where the pipeline is described.

## Two passes and a second reader

The paper's own procedure: one person reads the benchmark's documentation, then re-reads it while completing the worksheet, then at least two others examine the completed worksheet against the same sources.

Two passes and a second reader are the method, not a luxury. First-pass reading reliably imports the benchmark's framing along with its facts — you adopt its vocabulary, and its unstated assumptions become invisible because they have become yours.

## Not-stated is a finding

Every question has three possible answers:

- **Stated** — the sources say it. Cite it.
- **Implied** — the sources act as if it, without saying it. Mark it as your inference, and quote what it rests on.
- **Absent** — nothing. Record where you looked.

The third is the paper's most common result and its most useful one. Never fill a slot by inferring what the creators probably meant and writing it as though they said it. A worksheet that answers everything has usually stopped auditing and started reconstructing.

## Cite everything

Every answer carries a citation: document, section, page, or commit. An answer without one is your reconstruction and must be labelled as such.

This is what makes an audit contestable, and a finding nobody can contest is not worth much. When a claim rests on absence, cite the absence: name the sections you read that should have contained it.

## Audit the version, not the benchmark

Benchmarks change. Every finding is about the sources listed in `01_sources.md` at the versions recorded there. Where a finding might have been fixed in a later version you did not read, say so rather than implying currency.

## Separate the fault from the fix

Record what the sources do and do not establish before deciding what a user should do about it. Mixing the two produces findings that read as advocacy, and advocacy is easier to dismiss than evidence.
