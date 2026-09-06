# 01_intake — name what is being measured

One job: identify the response data, the run it serves, and which statistics it can support.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): the request as given, naming the eval or benchmark to measure
- Working (this run): the response data itself — an archive split, or a results file. Step 5 counts it
- Working (this run): the originating run's `RUN.md`, and its capability file — `02_capability.md` for a design run, `03_capability.md` for an audit
- Reference (every run): ../../_shared/openeval-schema.md
- Reference (every run): ../../worksheets/_index/log.md — for its column shape
- Reference (every run): ../../_templates/measure-run/ — the run folder you are about to copy

Do NOT load: the originating run's full worksheet. This stage needs what the eval *claims*, not how it was argued.

## Process
1. Create the run: copy `_templates/measure-run/` to `worksheets/measure-<slug>/`. The slug names what is measured.
2. Fill `RUN.md`: title, one-line summary, and every frontmatter field except `items`, `models`, `closed` and `status`. Set `direction` to `consume` or `emit`, and `serves` to the originating run's slug.
3. Add one line to `worksheets/_index/log.md` following the columns already in its table.
4. Record the source with an identifier a stranger could resolve: an archive split name and retrieval date, or a results file path plus the runner and version that produced it.
5. Count the matrix with `python _tools/validate.py <records>` or `--split <name>`, which reports the counts and which statistics they support. Record them here and in `RUN.md` frontmatter `items:` and `models:`. **Say what will not be computable**, rather than discovering it at stage 3.
6. Record the capabilities the originating run claims, verbatim from its capability file. Stage 3 checks the evidence against exactly this list.
7. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `01_intake.md` → the run folder

## Human check
Confirm the responses correspond to the eval the originating run describes — same items, same adaptation, same version. Measuring the wrong artefact produces evidence that looks authoritative and is about something else. If they diverge, say how, in the file.
