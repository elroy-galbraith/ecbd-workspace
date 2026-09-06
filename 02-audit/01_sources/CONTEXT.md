# 01_sources — fix what counts as evidence

One job: assemble the sources this audit reads, and declare the perspective it is written from.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): the request as given — a brief, a conversation, a ticket; it carries the use this audit is for
- Working (this run): the benchmark under analysis — paper, docs, repository, site, cards
- Reference (every run): ../../_shared/worksheet-questions.md (Framing)
- Reference (every run): ../../_shared/audit-method.md
- Reference (every run): ../../_shared/ecbd-framework.md
- Reference (every run): ../../worksheets/_index/log.md — for its column shape
- Reference (every run): ../../_templates/audit-run/ — the run folder you are about to copy

## Process
1. Create the run: copy `_templates/audit-run/` to `worksheets/audit-<slug>/`. Slug is kebab-case, prefixed `audit-`.
2. Fill `RUN.md`: title, one-line summary, and every frontmatter field except `second_reader` (stage 6), `closed` and `status`. Frontmatter is the queryable copy of what `01_sources.md` records in full; where they differ, `01_sources.md` is right.
3. Add one line to `worksheets/_index/log.md` following the columns already in its table. If the commented-out example rows are still there, delete them.
4. List every source with an identifier and a date — paper version, repo commit, docs retrieval date. Benchmarks change; an audit is of a version.
5. Draw the boundary. Restricting to the introducing paper limits findings to reporting practice; including code and issues audits a different object. State which and why.
6. Declare who is filing and from what perspective — creator, custodian, user, third party. This sets what counts as an acceptable "we don't know": a creator cannot answer Q5 with "not documented."
7. Record the use *you* are evaluating fitness for, if you have one. An audit against a concrete intended use answers a sharper question than an audit in general.
8. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `01_sources.md` → the run folder

## Human check
Confirm that another person can retrieve every source from what you wrote. Each one needs a URL, a version, or a commit. Nobody can contest an audit whose sources they cannot read. A finding nobody can contest has little value.
