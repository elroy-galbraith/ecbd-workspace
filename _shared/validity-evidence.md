# What counts as validity evidence

The bar for every SUPPORT question (Q5, Q8, Q11, Q14, Q17, Q20). The paper's headline finding is that benchmarks describe their choices, sometimes justify them, and almost never support them.

## The distinction that does the work

| | The question | What it produces |
|---|---|---|
| **Describe** | What did we decide? | A record of the decision |
| **Justify** | Why should this decision let the module fulfil its role? | A **hypothesis** |
| **Support** | What shows the hypothesis holds? | **Validity evidence** |

Justification without support is an untested assumption. That is permissible — as long as it is *labelled* as one. Laundering an assumption into an assertion is the failure this framework exists to prevent.

## Two kinds of evidence

**Theoretical** — conceptual work establishing that a construct is well-defined and well-grounded. Survey studies of what topical experts and end users actually consider important; literature conceptualising the capability; documented reasoning about contexts of use.

**Empirical** — experiments correlating benchmark measurements with some ground truth. Correlation between automatic metrics and human annotation. Ablations showing a measurement is sensitive to the capability and insensitive to irrelevant variation (prompt format, item order, surface form).

## Strength labels

Every SUPPORT answer gets one. Use them in the validity register and never round upward.

| Label | Means |
|---|---|
| `empirical-direct` | An experiment on *this* benchmark testing *this* hypothesis. |
| `empirical-transferred` | An experiment elsewhere whose conditions plausibly carry over. State why they carry over. |
| `theoretical` | Conceptual or survey work grounding the construct or the choice. |
| `precedent-only` | "Prior work does it this way." **Not validity evidence.** Record it as a gap. |
| `none` | No evidence identified. A finding, not an embarrassment. |

## `none` means unexamined, not unsupported

The commonest misreading, and it cost a real run. Evidence that a method **fails** is still evidence, and it takes the label its method earns — usually `empirical-direct`, with the finding recorded as negative.

A benchmark nobody has checked and a benchmark that has been checked and found wanting both look like `none` if you read the label as "nothing supports this." They are completely different situations, and the register exists to tell them apart. `audit-truthfulqa` recorded Q14 and Q20 as `none` while holding the measurements that bore on both; `measure-truthfulqa` corrected them to `empirical-direct` with negative findings.

So: `none` is for a slot where nobody has looked. If someone looked and the answer was bad, that is a result — label it as one.

## Precedent is not evidence

Following prior practice is the most common thing found in the SUPPORT slot, and it does not belong there. Methods well-justified in one context may be unsuited to another — particularly where the capabilities under measurement are defined differently. A metric being standard is a fact about the field, not about whether it captures your construct.

## Gaps are deliverables

Where no evidence exists, the honest outputs are: name the gap, state what experiment would close it, and estimate its cost. A worksheet whose SUPPORT answers are mostly `none` but which says so plainly is more useful than one that reads well and hides the same holes.
