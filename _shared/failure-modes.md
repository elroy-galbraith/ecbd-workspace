# Known failure modes

Findings from the paper's case studies (BoolQ, SuperGLUE, HELM) — §4.3 of [source/ECBD.pdf](source/ECBD.pdf). These are what the framework was built to catch, and they recur. Check a run against them at the validity-review or findings stage; each names the module it belongs to and the question that should have caught it.

| # | Failure | Module / Q | What it looks like |
|---|---|---|---|
| 1 | **Intended use vaguely specified** | Pre-Q, Q1–Q2 | Little description of who the users are or how they should interpret results. Sometimes explicit deferral — "it is up to users to identify pertinent scenarios and metrics." This makes the benchmark impossible to validate: you cannot assess whether results support an interpretation nobody stated. |
| 2 | **Sub-capabilities asserted, not connected** | Capability, Q3–Q4 | Complex capabilities broken into intermediate ones with the relationship left implicit. Constructs treated as self-evidently relevant, never defined. |
| 3 | **Construct collapsed into its measurement** | Capability, Q3 | The capability is defined in terms of the metric used to measure it, making the central question unaskable. |
| 4 | **Contested constructs left ungrounded** | Capability, Q4–Q5 | Fairness, bias, toxicity operationalised without reference to broader social context, as though the definitions were uncontroversial. |
| 5 | **Re-purposed data unjustified** | Content, Q7–Q8 | A dataset built for one purpose is re-used to measure something else, with no argument connecting it to the new capability. A yes/no QA dataset pressed into service for social bias. |
| 6 | **Adaptation unprescribed** | Adaptation, Q9–Q11 | The benchmark does not specify how objects of evaluation are prompted or adapted, leaving users to choose. Since models are demonstrably sensitive to prompt format, results become incomparable across users. Where a benchmark declines to prescribe, users should report what they employed. |
| 7 | **Assembly taken as self-evident** | Assembly, Q12–Q14 | Splits and caps stated without rationale — "a maximum of 1,000 items per dataset" with no account of the selection process, or inherited train/dev/test splits whose original construction is undocumented. |
| 8 | **Evidence methods justified by precedent** | Evidence, Q16–Q20 | Metrics and aggregation described as "standard" or "default," or chosen to follow prior work, with no argument that they capture *these* capabilities. Applies to new metrics too: novel constructions still need a case that they measure what they claim. |
| 9 | **Validity evidence absent entirely** | All SUPPORT questions | Evidence-gathering not described, or acknowledged as future work. Present in all three benchmarks examined. |

## Two failure modes of the worksheet itself

**Checklist mode.** Answering all twenty questions perfunctorily to produce a document. The questions exist to force reflection; a fluent worksheet that surfaces no tension has failed even if every field is populated.

**Coverage confusion.** ECBD assesses validity, not overall quality. The things that matter and sit outside these twenty questions are listed once, in `ecbd-framework.md` under "What this is not". Note them separately rather than assuming a clean worksheet means a sound benchmark.
