# ecbd-workspace

A workspace for designing evals and auditing benchmarks under **ECBD** — Evidence-Centered Benchmark Design ([Liu et al., ACL 2024](https://aclanthology.org/2024.acl-long.861/)).

The premise: a benchmark is a measurement instrument, not a dataset. The question worth answering is not "is the score high?" but "can this score be interpreted the way we intend to interpret it?" ECBD turns that into twenty questions across five modules, and this workspace turns those questions into a process you can actually run.

**Humans start here. Agents start at [CLAUDE.md](CLAUDE.md)** — it holds the routing table, and duplicating it here would give us two maps that disagree within a month.

## What's in the box

Three pipelines over one shared framework:

- **[01-design/](01-design/CONTEXT.md)** — eight stages taking a fuzzy "we need to measure X" to a justified eval design *plus the runnable eval it justifies*: items, prompts, scorer, aggregator.
- **[02-audit/](02-audit/CONTEXT.md)** — six stages taking a benchmark someone else built to a findings report and a fitness verdict for a use you name.
- **[03-measure/](03-measure/CONTEXT.md)** — four stages turning item-level responses into validity evidence, written back into the run that needed it. This is what turns a SUPPORT question from `none` into a measurement.

The first two walk the same twenty questions. Every run becomes one folder in `worksheets/`.

### Maturity, stated honestly

| | State |
|---|---|
| `02-audit/` | **Proven.** Run end to end on TruthfulQA, including item-level psychometrics. Two loop-backs, both caught real errors. |
| `01-design/` | **Scaffolded, never run.** Contracts have survived three adversarial cold-agent walk-throughs and zero real use. It is the harder half — it makes decisions rather than reading them — so expect loop-backs the audit line did not need. |
| `03-measure/` | **Scaffolded, never run as a pipeline.** Its contracts are derived from analysis that worked — `audit-truthfulqa` ran it inline from audit stage 5 — but no `measure-` run exists. The emit path additionally waits on `01-design/` producing a build. |
| `_tools/` | **Working, narrow.** `item_analysis.py` assumes OpenEval's `bleurt-20` record shape; other benchmarks need their own accessor. |

## What this actually gives you

Most eval tooling tells you *what a model scored*. This tells you **whether a score means what it is being asked to mean** — and for any benchmark with OpenEval coverage, it can answer that with measurements rather than argument.

The first real run makes the point better than a description. Auditing TruthfulQA for model selection produced:

- No adjacent pair in a 145-model ranking is statistically distinguishable. Two models need roughly a **7-point gap** to separate; the median gap between adjacent ranks is **0.12 points**.
- **The entire top ten fits inside the uncertainty of a single model's score.**
- Split the item set in half at random and the two halves **swap a given model pair's order 21% of the time**.
- **18% of items have zero or negative discrimination**; 48% are below 0.1. Length is carrying the reliability, not the content.
- The one metric the authors validated as rank-preserving is an unreleased fine-tune of a retired model. **It cannot be run by anyone.**

None of that is visible from an aggregate score, and none of it required trusting the auditor's judgement — it is arithmetic over item-level data, reproducible with one command.

The same run also found TruthfulQA to be *better designed* than all three benchmarks in ECBD's own case studies. Both conclusions are true at once, which is the point: the framework separates "is this well built?" from "is this fit for what I am about to do with it?"

## What it cannot do yet

- **Execute** an eval. `01-design/` ends at a runnable build and `03-measure/` starts from results; nothing in between runs the models. That is deliberate — running evals means credentials, spend, rate limits and caching, and every team already has a harness. Wire yours in through [_shared/results-contract.md](_shared/results-contract.md).
- **Prove the emit path.** `03-measure/` can emit OpenEval records, but no design run has produced a build to emit from.
- **Generalise the analysis** beyond OpenEval's `bleurt-20` record shape.
- **Clear commercial use** of archive data. OpenEval is CC-BY-NC-4.0; unresolved.

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
