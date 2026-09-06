# The ECBD worksheet — canonical questions

The single source of truth for Q1–Q20. Stage contracts name which questions they cover; they never restate the questions. Wording follows Appendix A of [source/ECBD.pdf](source/ECBD.pdf), lightly generalised from "benchmark creators" to "designers" so the same bank serves both pipelines.

**Reading it in design mode:** the questions are prompts for decisions you are about to make.
**Reading it in audit mode:** they are prompts for decisions someone already made — and "the sources do not say" is a finding, not a failure to answer.

## Framing (before Q1)

- **Name and reference(s).** What is the benchmark called, and what sources ground this worksheet — paper, docs, blog posts, repository?
- **Who is filing, and from what perspective?** Creator, custodian, user, or third-party analyst? The answer changes what counts as an acceptable "we don't know."

## A.1 Intended use

- **Q1** — Who/what are the intended objects of evaluation? Elaborate on their assumed capabilities, and any demographic information where the objects are human.
- **Q2** — What is the intended use of the benchmark, and who are the intended users? Results are meant to provide insight about the objects of evaluation: how are users meant to use that insight?

## A.2 Capability module

- **Q3 — DESCRIBE.** i) What are the capabilities of interest? ii) How is each one defined, and under what context?
  - Recommended follow-ups: How does this definition differ from other existing definitions of the same capability? How does this capability differ from other similarly defined capabilities?
- **Q4 — JUSTIFY.** How are the capabilities of interest connected to the intended use (Q2)? Are the capabilities theoretically attainable by the objects to be evaluated?
- **Q5 — SUPPORT.** What validity evidence supports the choice and definition of the capabilities of interest?

## A.3 Content module

- **Q6 — DESCRIBE.** i) Characterise the test items — what data is available, how it is obtained. ii) Which capabilities of interest does each item aim to capture? An item may target one or several of those listed in Q3.
- **Q7 — JUSTIFY.** How does each test item elicit evidence about its target capabilities? Justify via the characteristics of the items (Q6).
- **Q8 — SUPPORT.** What evidence supports the content validity of the test items — i.e. that the items capture the capabilities of interest? Often established by analysis from external experts or benchmark users.

## A.4 Adaptation module

- **Q9 — DESCRIBE.** Given an input, how are the objects of evaluation adapted or instructed to produce the output?
- **Q10 — JUSTIFY.** Elaborate on the suitability of the adaptation methods for *all* intended objects of evaluation.
- **Q11 — SUPPORT.** What validity evidence supports the choice of adaptation methods?

## A.5 Assembly module

- **Q12 — DESCRIBE.** How many test items are chosen to assemble the subset used for evaluation? What factors inform this selection?
- **Q13 — JUSTIFY.** How does the assembly method ensure the subset elicits sufficient evidence for *all* capabilities of interest?
- **Q14 — SUPPORT.** What validity evidence supports the choice of assembly methods?

## A.6 Evidence module

### A.6.1 Extraction

- **Q15 — DESCRIBE.** For each test item: i) What responses are captured and used for evidence extraction? (Generated text, token probabilities, selections, running time, latency…) ii) How is evidence extracted and represented?
- **Q16 — JUSTIFY.** How does the extracted evidence capture the capabilities of interest?
- **Q17 — SUPPORT.** What validity evidence supports the choice of evidence extraction method?

### A.6.2 Accumulation

- **Q18 — DESCRIBE.** How is evidence accumulated to draw insights about the objects of evaluation in terms of the capabilities of interest?
- **Q19 — JUSTIFY.** How does the accumulation method capture the capabilities of interest?
- **Q20 — SUPPORT.** What validity evidence supports the choice of evidence accumulation method?

## Answering rules

- An honest **"no evidence exists"** on any SUPPORT question is a valid answer and a finding. Record it as a gap in the validity register; do not manufacture a justification to fill the slot.
- Distinguish **justification** (a hypothesis: why this should work) from **support** (evidence that it does). Restating the decision in different words is neither.
- Every capability named in Q3 must be traceable through Q6 (items target it), Q13 (assembly covers it) and Q19 (accumulation measures it). A capability that drops out along the way is a broken instrument.
