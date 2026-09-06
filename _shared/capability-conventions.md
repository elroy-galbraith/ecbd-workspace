# Defining capabilities well

The capability module is the pivot: it is the only module connecting the benchmark to its intended use, and every other module is judged against what it names. The paper's deepest findings are all here.

## A capability definition must be two things

**Well-matched to the intended use.** If the intended use is deciding whether to deploy an automatic summariser for medical records, "general language understanding" is not the capability — it is a proxy nobody has connected to the decision.

**Well-grounded.** Capabilities are contested and context-dependent. Who are the users of the evaluated system, and what are their needs? A definition asserted without grounding cannot be argued with, which is a defect rather than a convenience.

## Write each capability as a card

For every capability of interest, record:

- **Name** — the term used, exactly as it will appear downstream.
- **Definition** — what it means here, in one or two sentences.
- **Context** — users, stakeholders, domain, linguistic phenomena the definition assumes.
- **Distinguished from** — how it differs from other existing definitions of the same term, and from similarly named neighbouring capabilities.
- **Grounding** — the theoretical or empirical basis. `none` is an answer.
- **Attainability** — is this capability theoretically possible for the intended objects of evaluation? Measuring something an object cannot in principle have produces a number about the instrument, not the object.

## Decomposition: name the edges

Complex capabilities get broken into intermediate ones that are easier to measure. Splitting is fine; leaving the connection unexplained is not.

Whenever a capability is decomposed, state the relation explicitly: why do these sub-capabilities contribute to the parent, and do they exhaust it or merely sample it? SuperGLUE aims at "general-purpose language understanding" and introduces sub-constructs such as "causal reasoning" as if their relevance were self-evident, never defining them or explaining the connection. HELM does better — it draws an explicit line from "practical utility" to seven intermediate capabilities — though the relationships still invite interrogation.

Draw the tree. Every edge is a claim; unlabeled edges are where validity leaks out.

## Do not collapse construct into measurement

A construct and the thing that measures it are different objects. Describing accuracy — the construct — as "an umbrella term for the standard accuracy-like metric" defines a capability by its measurement, which makes it impossible to ask whether the measurement captures the capability. Name the construct first, in language that does not mention any metric. Choose the metric later, in the evidence module, and justify the connection there.

## Contested constructs need extra care

Fairness, bias, toxicity, harm, quality, helpfulness: more often than not these are contested, and depend on the context in which they are applied. Conceptualising them without reference to broader social context is itself a validity threat. If a run names one, its card must say whose definition is being used and who was consulted — or record that nobody was.

## The traceability test

At the end of a run, every capability named here must appear in:

- **Q6** — items that target it
- **Q13** — an assembly method that covers it
- **Q19** — an accumulation method that measures it

A capability that appears in the definition and nowhere else is decorative. A measurement that appears downstream with no capability upstream measures something nobody has named.
