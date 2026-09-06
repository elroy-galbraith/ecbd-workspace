# How this workspace writes

Some text here is held to Simplified Technical English. Most is not, on purpose. This file says which is which, so the next person writing does not have to guess.

## The standard

ASD-STE100, `lite` profile. Sentences under 25 words. Active voice. One term for one idea. No idioms and no phrasal verbs where a plain verb exists.

The rules that carry most of the benefit:

1. **One word for one idea.** Choose a term and keep it. Variation is good style in an essay and a defect here — the reader cannot tell whether you renamed a thing or introduced a new one.
2. **One idea per sentence.** Split at the conjunction. Do not compress by removing articles.
3. **Active voice, and name who acts.** "The gateway validates the token" is the same length as "the token is validated" and answers one more question.
4. **No idioms.** "Comes apart", "buys nothing", "cuts the other way" all fail for a reader working in a second language, and they survive a spell check.

## What is held to it

| Text | Why |
|---|---|
| `_shared/interpreting-item-analysis.md` | Written for non-experts, read under time pressure, at the moment a decision is made |
| Every `## Human check` in a stage contract | Instructions to a person. Procedures are what STE was built for |
| The `DIAGNOSIS` lines in `_tools/item_analysis.py` | Read at a glance, often by someone who did not run the analysis |

## What is not, and why that is deliberate

**Run worksheets.** Audit findings and analyses are arguments, not procedures. They turn on distinctions that survive only in careful prose — "the distance between those two sentences is the result of this audit" says something that no short-sentence version says. They also quote source papers, and STE forbids rewriting a quotation.

**Decision records.** Same reason. A record of why a choice was made has to carry the reasoning that a later reader will test.

**Reference files other than the interpretation guide.** `failure-modes.md`, `capability-conventions.md` and the rest are read by an agent loading a stage contract, not by a person under pressure. STE costs nuance and buys nothing there.

**`README.md`.** Mixed. Its job is to orient a new reader, which needs some flow. Keep sentences short where it costs nothing, but do not flatten it.

## Technical Names are kept

STE keeps domain terms that have no plain equivalent. Define each one once, then never vary it. In this workspace these are Technical Names and stay unchanged:

*capability*, *construct*, *validity*, *discrimination*, *reliability*, *item*, *facet*, *adaptation*, *accumulation*, *KR-20*, *point-biserial*.

Do not replace a precise term with a vague one to satisfy a word list. That trades meaning for compliance.

## Checking

```bash
python <skill-dir>/scripts/check_ste.py <file> --profile lite
```

On Windows set `PYTHONIOENCODING=utf-8` first, or the checker fails on any non-ASCII character.

Read the output with judgement. Its noun-cluster rule joins words across sentence boundaries and bold markers, so it reports clusters that are not there. Sentence length, passive voice, idioms and terminology drift are reliable. Terminology drift is the most valuable of the four and the easiest to miss by eye.

The checker cannot tell whether the meaning survived. Read the result yourself before you accept it.
