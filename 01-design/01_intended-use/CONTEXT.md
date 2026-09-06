# 01_intended-use — settle what this eval is for

One job: state the intended use precisely enough that every later decision can be judged against it.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): the request as given — a brief, a conversation, a ticket
- Reference (every run): ../../_shared/ecbd-framework.md
- Reference (every run): ../../_shared/worksheet-questions.md (Framing, Q1–Q2)
- Reference (every run): ../../worksheets/_index/log.md — for its column shape
- Reference (every run): ../../_templates/design-run/ — the run folder you are about to copy
- Reference (if it exists): ../../_shared/house-context.md

Do NOT load: other stages' references, prior runs, the source PDF.

## Process
1. Create the run: copy `_templates/design-run/` to `worksheets/design-<slug>/`. Slug is kebab-case, prefixed `design-`.
2. Fill `RUN.md`: the title and its one-line summary, then frontmatter `slug`, `opened`, `owner`. Leave `capabilities:` empty — stage 8 fills it; `objects_of_evaluation:` is filled at step 5.
3. Add one line to `worksheets/_index/log.md` following the columns already in its table. If the commented-out example rows are still there, delete them.
4. Answer the framing questions and Q1–Q2 into `01_intended-use.md`.
5. Name the objects of evaluation concretely — which systems, which versions, under what conditions. "LLMs" is not an answer. Copy the list into `RUN.md` frontmatter `objects_of_evaluation:`; stage 4 answers Q10 against it.
6. State the decision the results will inform, and who makes it. If no one acts differently based on the outcome, say so plainly here rather than discovering it at stage 7.
7. Record what would make this eval a waste of effort. That line constrains scope more than any other.
8. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `01_intended-use.md` → the run folder

## Human check
Ask the person who requested the eval one question: "if this result is good, what will you do differently?" A vague answer means the intended use is not settled. Stage 2 will then inherit that vagueness. Edit this file directly. The next stage reads whatever you leave here.
