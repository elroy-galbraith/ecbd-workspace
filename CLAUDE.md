# ecbd-workspace

A workspace for designing evals and auditing benchmarks under ECBD — Evidence-Centered Benchmark Design. Each run produces one worksheet record; design runs also produce the runnable eval that worksheet justifies.

Built on ICM: folders carry sequencing, hierarchy carries context, files carry state. The structure is the documentation — if something needs explaining, it goes in that folder's `CONTEXT.md`, not in your head.

## Where things live

| Folder | What it holds |
|---|---|
| `01-design/` | pipeline: design a new eval, eight stages, ends in runnable artefacts |
| `02-audit/` | pipeline: analyse an existing benchmark, six stages, ends in findings |
| `_shared/` | factory: the framework, the 20 questions, the glossary, the rules |
| `_templates/` | blank run folders — a new run is a copy, not a blank page |
| `_tools/` | runnable analysis over item-level data; the only code here |
| `worksheets/` | product: one folder per run, plus `_index/log.md` |
| `setup/` | one-time configuration of house context |
| `CONTEXT.md` | this workspace in one screen — read it once, before your first run |
| `README.md` | human onboarding — orientation, not routing. Point people here, don't read it to work |

## Route by what you were asked

| If | Go to | Then stop at |
|---|---|---|
| designing a new eval | `01-design/CONTEXT.md` | the stage's human check |
| analysing someone else's benchmark | `02-audit/CONTEXT.md` | the stage's human check |
| auditing an eval built here | `02-audit/CONTEXT.md`, sources = its own record | the stage's human check |
| mid-run, stage N approved | stage N+1's `CONTEXT.md` | the stage's human check |
| asked for status | `worksheets/_index/log.md`, then each run's `RUN.md` | report what exists and how far it got |
| asked how the two pipelines relate | `CONTEXT.md` | — |
| asked what a term means | `_shared/glossary.md` | — |
| first use in a new team or domain | `setup/questionnaire.md` | answers written to `_shared/house-context.md` |

## Loading discipline

Read the stage contract, its named inputs, and its named references. Nothing else. A stage contract's Inputs section is the whole context budget — if you are tempted to read a neighbouring stage or a prior run, the contract is wrong and should be fixed rather than worked around.

Never read `_shared/source/ECBD.pdf` during a run. It is the provenance record; `_shared/ecbd-framework.md` is the working reference.

## The one rule

Nothing moves to the next stage until a person has read the output of the last one. The gates are the method — an eval whose capability definitions were never argued with is exactly the artefact ECBD exists to prevent.
