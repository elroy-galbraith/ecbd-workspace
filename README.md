# ecbd-workspace

A workspace for designing evals and auditing benchmarks under **ECBD** — Evidence-Centered Benchmark Design ([Liu et al., ACL 2024](https://aclanthology.org/2024.acl-long.861/)).

The premise: a benchmark is a measurement instrument, not a dataset. The question worth answering is not "is the score high?" but "can this score be interpreted the way we intend to interpret it?" ECBD turns that into twenty questions across five modules, and this workspace turns those questions into a process you can actually run.

**Humans start here. Agents start at [CLAUDE.md](CLAUDE.md)** — it holds the routing table, and duplicating it here would give us two maps that disagree within a month.

## What's in the box

Two pipelines over one shared framework:

- **[01-design/](01-design/CONTEXT.md)** — eight stages taking a fuzzy "we need to measure X" to a justified eval design *plus the runnable eval it justifies*: items, prompts, scorer, aggregator.
- **[02-audit/](02-audit/CONTEXT.md)** — six stages taking a benchmark someone else built to a findings report and a fitness verdict for a use you name.

Both walk the same twenty questions. Every run becomes one folder in `worksheets/`.

## Why folders instead of one long prompt

The structure *is* the orchestration. Numbered folders carry sequence, hierarchy carries context scoping, and plain markdown files carry state — so one agent reading the right files at the right moment does the work a multi-agent framework would do in code, and you can see the whole system state by opening a folder.

The practical payoff: each step loads 2,000–8,000 tokens of exactly what it needs, instead of 30k of mostly-irrelevant context. The method is [ICM](https://arxiv.org/abs/2603.16021) (Van Clief & McDermott).

## Onboarding — about fifteen minutes

Read in this order:

1. **[CONTEXT.md](CONTEXT.md)** — the workspace in one screen: the two lines, why they're shaped differently, where product lives.
2. **[_shared/ecbd-framework.md](_shared/ecbd-framework.md)** — the framework itself. The five modules, and the describe → justify → **support** triad that most benchmarks stop two-thirds of the way through.
3. **[_shared/worksheet-questions.md](_shared/worksheet-questions.md)** — the twenty questions, skimmed. You don't need to memorise them; each stage tells you which it covers.
4. **[_shared/failure-modes.md](_shared/failure-modes.md)** — the nine documented ways benchmarks go wrong. This is the fastest way to understand what the workspace is *for*.

Keep [_shared/glossary.md](_shared/glossary.md) open the first time. ECBD draws distinctions that ordinary usage blurs — *capability* vs *capability evidence*, *response* vs *result* — and the framework's value comes from those distinctions holding.

## The one piece of code

The workspace is markdown with one exception: [_tools/item_analysis.py](_tools/item_analysis.py) computes item difficulty, discrimination, reliability and ranking stability from OpenEval's item-level data. It needs only pandas, pyarrow, numpy and scipy. Audits of benchmarks with archive coverage can answer SUPPORT questions with measurements instead of absence.

## Setting up for a team

Answer **[setup/questionnaire.md](setup/questionnaire.md)** once. Seven questions about what you evaluate, who reads results, what runner your builds target, and where your bar for validity evidence sits. The answers become `_shared/house-context.md`, which nine stages load.

Skip it for a one-off — the defaults work without it.

## Your first run

Tell the agent what you want, in your own words:

> "Design an eval measuring whether our support summariser produces faithful summaries."

> "Audit whether MMLU is fit for choosing a model for our legal research product."

It routes itself from `CLAUDE.md`, copies the right template into `worksheets/`, and starts at stage 1. You don't need to know the stage names.

## What the workspace asks of you

This is the part that surprises people: **it stops constantly, on purpose.**

Every stage ends at a human check — one concrete act, not a vague "review." Read the capability definition to a domain expert and ask them to argue with it. Answer three test items wrongly on purpose and see whether the wrong answer is better explained by something other than lacking the capability. Take the headline number and write the sentence a user would say about a system that scores well.

Those gates are the method, not friction around it. An eval whose capability definitions were never argued with is precisely the artefact ECBD exists to prevent. Correction is also cheapest early — a definition fixed at stage 2 costs a conversation; the same fix after items are written costs the item pool.

Expect to loop back. A validity review that sends you to stage 2 is the pipeline working. Record it in the run's `RUN.md`.

## What "done" looks like

A **design run** ends with a completed worksheet, a validity register listing every gap honestly, and a `build/` folder holding the runnable eval — with a traceability table mapping each artefact to the decision that justifies it, and the supported-interpretation sentence travelling alongside the score.

An **audit run** ends with a completed worksheet, ranked validity threats, and a verdict: what these results support, what they don't, and what a user can do about it without the creators' involvement.

Expect a lot of `none` in the SUPPORT column. That is the honest finding, not a failure — and a register that says so plainly is more useful than one that reads well and hides the same holes.

## Status

Read `worksheets/_index/log.md` for what runs exist, then each run's `RUN.md` for how far it got. `RUN.md` is the only file recording a run's state; there is deliberately no status column in the log.

## Scope

ECBD assesses **validity**. It does not cover item provenance and consent, privacy, or reliability under repetition — all real requirements, all outside these twenty questions. Every run records them separately so a clean worksheet never implies a sound benchmark.

## Provenance

The paper is at [_shared/source/ECBD.pdf](_shared/source/ECBD.pdf) — the citation of record, deliberately never loaded during a run. `_shared/ecbd-framework.md` and `_shared/worksheet-questions.md` are the working references. Reference implementation and the authors' completed worksheets: [github.com/isle-dev/ECBD](https://github.com/isle-dev/ECBD).
