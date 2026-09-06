# ECBD — the framework in one page

Source: Liu, Blodgett, Cheung, Liao, Olteanu & Xiao (2024), *ECBD: Evidence-Centered Benchmark Design for NLP*, ACL 2024, pp. 16349–16365. Full paper: [source/ECBD.pdf](source/ECBD.pdf). Adapted from Evidence-Centered Design in educational testing (Mislevy, 2003).

## The core reframe

Benchmarking is **the process of gathering capability evidence from objects of evaluation** about whether, or to what degree, they have capabilities of interest. A benchmark is not a dataset — it is a measurement instrument. Capabilities are constructs: unobservable, so measured only indirectly through observable behaviour.

The question a benchmark must survive is not "is the score high?" but **"can these results be interpreted the way we intend to interpret them?"** That is validity.

## The precondition: intended use

Not a module, but must be settled first — every downstream choice is judged against it. Three things: who/what the objects of evaluation are, who the users are, and how results should be interpreted and used.

Skip this and design choices get made because they are convenient or conventional, producing a benchmark that serves no purpose in particular.

## The five modules

| Module | Specifies | Its role — what it must accomplish |
|---|---|---|
| **Capability** | The constructs the benchmark aims to measure | Connect the benchmark to its intended use |
| **Content** | The pool of available test items | Each item elicits capability evidence about the capabilities it targets |
| **Adaptation** | How objects of evaluation are instructed/adapted to respond | Methods are well-suited to *all* objects of evaluation, disadvantaging none |
| **Assembly** | Which items from the pool are actually used | The selected set elicits *sufficient* evidence to measure the capabilities |
| **Evidence** | How evidence is extracted from responses, then accumulated | Extracted evidence captures targeted capabilities; accumulated evidence captures the capabilities of interest |

The evidence module has two components: **extraction** (per item: response → observable variable) and **accumulation** (across items: variables → measurement).

## The triad — applied to every module

Each module is worked through three actions. Most benchmarks do the first and stop; the paper's central finding is that the third is almost always missing.

- **Describe** — what design decisions were made?
- **Justify** — why? This forms a *hypothesis*: that these decisions let the module fulfil its role.
- **Support** — what validity evidence shows the hypothesis holds? See [validity-evidence.md](validity-evidence.md).

## How the pieces connect

Intended use constrains the capability module. The capability module constrains everything else: content items target capabilities, assembly must cover them, and accumulated evidence must land back on them. Evidence flows the other way — objects of evaluation receive input (content, shaped by adaptation, selected by assembly) and produce output, from which evidence is extracted and accumulated.

A closed loop. If accumulated evidence does not map back to the capabilities named at the start, the instrument measures something other than what it claims.

## What this is not

Not a checklist. The questions exist to force reflection and make tacit assumptions explicit; answering all twenty perfunctorily is the documented failure mode the authors warn about. Also not a complete quality assessment — item provenance and consent, privacy, and reliability all matter and sit outside ECBD.
