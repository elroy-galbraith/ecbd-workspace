# Glossary

ECBD terminology, from Table 1 of [source/ECBD.pdf](source/ECBD.pdf). Use these words precisely in worksheets — the framework's value comes from the distinctions they draw.

| Term | Meaning |
|---|---|
| **Objects of evaluation** | Models, systems, people, etc. that are to be evaluated. |
| **Capability** | Quality criteria, ability, skill, etc. that characterises the objects of evaluation. Very often neither observable nor directly measurable. |
| **Capability evidence** | Evidence indicating whether, or to what degree, an object of evaluation has the capability of interest. A model detecting the grammatical error in "their going to the mall" is evidence supporting the belief that it has grammatical knowledge. |
| **Benchmarking** (verb) | The process of gathering capability evidence from objects of evaluation about their capabilities. |
| **Benchmark** (noun) | A collection of measurement instruments that supports that process. |
| **Benchmark results** | The final product: numerical scores, rankings, or categorisations. They inform users about the objects of evaluation. |
| **Validity evidence** | Evidence supporting whether the benchmark results can be interpreted as intended, and whether the benchmark can be used as intended. May be theoretical or empirical. |
| **Validity; validation** | Validity is the degree to which all accumulated validity evidence supports the intended interpretation of results for the intended use. Validation is the process of accumulating that evidence. |
| **Test item** | A single evaluation instance that objects of evaluation are asked to perform or respond to, in order to obtain outputs or behaviours. |
| **Response** | Outputs or behaviours produced by an object of evaluation in response to a test item. Expected to be observable — a matrix of token probabilities and the decoded text are both possible responses. *Which* response to capture is a design decision. |
| **Context** (capability module) | Where and how the objects of evaluation are intended to be used or operate: types of users, other stakeholders, domain of application, the linguistic phenomena the systems are meant to represent. Capability definitions vary greatly by context — informativeness differs for expert vs non-expert readers. |

## Terms this workspace adds

| Term | Meaning |
|---|---|
| **Run** | One pass through a pipeline, producing one worksheet record in `worksheets/`. |
| **Design run** | A run through `01-design/` that creates a new eval: worksheet plus runnable artefacts. |
| **Audit run** | A run through `02-audit/` that analyses an existing benchmark against the same 20 questions. |
| **Validity register** | The per-run ledger of every SUPPORT answer, its strength, and every acknowledged gap. The honest summary of what the instrument has not earned. |
| **Cost of failure** | What a wrong result costs, in both directions, and who carries each. A false pass and a false block land on different people. Two answers, never one. See [decision-cost.md](decision-cost.md). |
| **Cost asymmetry** | The ratio between those two costs, with a direction. Carries a label — `elicited`, `derived`, `assumed` or `absent` — on the same discipline as a strength label. |
| **Operating point** | The score at which someone acts, the loss ratio that justifies it, and the switching condition that would move it. All three, or it is a number someone typed. |

## Terminology drift to avoid

ECBD deliberately renames parts of the educational-testing CAF it adapts. Keep to ECBD's words: **module** (not *model*, which in NLP means the thing being evaluated) and **content** (not *task*, which in NLP means a category of problems rather than a single test item).
