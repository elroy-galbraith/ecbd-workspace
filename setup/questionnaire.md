# Setup — configure the factory once

Answer these once per team or domain. The answers are written to `_shared/house-context.md`. Nine stages load it if it exists — all eight of `01-design/`, plus `02-audit/06_findings/`. Those are the points where a house default actually changes a decision. This configures the factory; the product is what each run emits.

Skip this if you are running a one-off. The defaults in `_shared/` work without it.

---

## 1. What do you mostly evaluate?
Systems, versions, modalities. If it varies, say what the common case is and what the exceptions look like.

[ANSWER HERE]

## 2. Who reads eval results, and what do they decide?
Ship/no-ship, model selection, regression gates, external publication. Different readers need different things from the accumulation step — a gate needs a threshold, a publication needs an interval.

[ANSWER HERE]

## 3. What runner do the builds target?
The harness, framework or scripts a `build/` folder must fit. Item file format, scorer interface, how results are emitted. Stage 8 adapts to this — the requirements in its build contract do not bend, but the file formats do.

[ANSWER HERE]

## 4. House rules on validity evidence
Is `precedent-only` ever acceptable for a shipping eval? Is a judge model allowed without human-correlation evidence, and if so under what conditions? Where is the bar for a gate versus an exploratory measurement?

Write the rule, not the aspiration. A rule nobody follows is worse than an acknowledged gap.

[ANSWER HERE]

## 5. Capability vocabulary already in use
Terms your team already uses for constructs — helpfulness, faithfulness, safety, groundedness. List them with the definition currently in play, even if it is loose. Stage 2 will sharpen them; it should not silently redefine them.

[ANSWER HERE]

## 6. Standing constraints
Compute, budget, latency, annotation capacity, data access, anything that reliably limits assembly. Naming these here stops every run from rediscovering them at stage 5 and presenting a resource limit as a methodological choice.

[ANSWER HERE]

## 7. Who is the second reader?
The audit pipeline requires one at `02-audit/06_findings`, and the design pipeline's stage 2 human check wants someone who will argue. Name people, not roles.

[ANSWER HERE]

---

## Writing the answers

Copy them into `_shared/house-context.md` under the same headings. Keep it under a page. Nine stages load it, and a bloated house context is the fastest way to blow the token budget the contracts protect.
