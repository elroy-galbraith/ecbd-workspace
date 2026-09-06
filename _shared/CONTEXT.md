# _shared — the factory

Reference material. Stable across runs, loaded by contract, never edited during a run.

The "Loaded by" column reflects what the stage contracts actually list, checked against them. If you change a contract's Inputs, change this row — a catalog that lies about its own shelf is worse than no catalog.

| File | Read it when | Loaded by |
|---|---|---|
| `worksheet-questions.md` | you need the exact wording of Q1–Q20 | design 1–7, audit 1–5 |
| `validity-evidence.md` | you are answering or grading a SUPPORT question | design 2–7, audit 3–6, measure 3–4 |
| `ecbd-framework.md` | you need what a module is for, how the pieces connect, and what ECBD does not cover | design 1 and 7, audit 1, 2 and 6 |
| `capability-conventions.md` | you are defining or assessing capabilities | design 2, audit 3 |
| `failure-modes.md` | you are synthesising findings or reviewing validity | design 7, audit 4 and 6 |
| `audit-method.md` | you are answering any question in an audit | audit 1–6 |
| `openeval-schema.md` | you are reading or writing item-level records | measure 1, 2, 4 |
| `results-contract.md` | you need to know what a runner must emit | design 8, measure 1 and 2 |
| `glossary.md` | a term is ambiguous — capability vs capability evidence, response vs result | nothing; read on demand, by anyone |
| `house-context.md` | it exists — team defaults from `setup/`; absent until `setup/` is run | design 1–8; audit 6; measure 4 |
| `source/ECBD.pdf` | never, during a run | nothing |

## Why the PDF is not a reference

`source/ECBD.pdf` is the provenance record — it settles disputes about what the framework actually says, and it is what you cite when someone asks where this came from. It is not a working file. Seventeen pages of paper at a stage boundary is precisely the context-stuffing this workspace is built to avoid; `ecbd-framework.md` and `worksheet-questions.md` carry everything a run needs.

## Why the glossary has no loader

It is the one file here meant for a person mid-sentence rather than an agent mid-stage. Adding it to fourteen contracts would spend tokens on every run to answer a question most runs never ask. `CLAUDE.md` routes to it on demand.

## Changing these files

They are load-bearing for every future run. Two rules:

- **One home per fact.** The 20 questions live in `worksheet-questions.md` alone; the strength labels in `validity-evidence.md` alone; the nine failure modes in `failure-modes.md` alone; the out-of-scope list in `ecbd-framework.md` alone. Stage contracts and templates cite them and never restate them. Where a template must show a value at the point of use — an enum in a form field — it says which file is the authority.
- **Changes are not retroactive.** Completed records reflect the rules as they stood. Note a material change here in the run log so a later reader can tell why two records answer the same question differently.
