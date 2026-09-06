# What a build must contain

Harness-agnostic requirements. Adapt file formats to whatever runner the house uses — recorded in `_shared/house-context.md`, if `setup/` has been run; ask otherwise — but do not drop a requirement to fit a tool.

## Structure

```
build/
├─ README.md              how to run, what it emits, traceability table
├─ items/                 the pool + selection manifest
├─ adaptation/            prompts, config, parser
└─ scoring/               extraction scorer, accumulation logic
```

## Non-negotiables

**Every item declares its capabilities.** A `capabilities: [...]` field per item, using names exactly as written in `02_capability.md`. This is what makes the per-capability breakdown possible, and what keeps the traceability test checkable months later.

**Per-capability results survive to the output.** A composite may be reported, but never alone and never as the only thing computed. Aggregating away the breakdown discards the structure the whole worksheet exists to establish.

**Adaptation is fully pinned.** Prompts, decoding parameters, few-shot selection and seed live in files, not in someone's shell history. If a parameter is deliberately left open, the runner records what was used and emits it with the results.

**The scorer is separable from the aggregator.** Extraction and accumulation are distinct decisions with distinct justifications. Fusing them into one function makes it impossible to change one and re-justify only that one.

**Results are OpenEval records.** Whatever runs this eval must emit records matching `_shared/openeval-schema.md`, carrying the rendered prompt and the generation parameters actually used. There is no second accepted format; if your harness emits rows, the adapter that nests them is part of the build. This is what lets `03-measure/` turn a SUPPORT gap into a measurement later.

**The caveat travels with the number.** The supported-interpretation sentence from the validity register appears in `README.md` and in the results output. A score that escapes its worksheet becomes precedent for someone else's benchmark.

## Traceability table

`README.md` ends with a table: artefact → worksheet section → the decision it implements. An artefact with no worksheet section behind it means an undocumented design decision was made during implementation. Send it back to the stage that owns it.
