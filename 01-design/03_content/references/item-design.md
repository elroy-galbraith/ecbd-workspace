# Designing items that carry evidence

An item earns its place when a response to it changes what you believe about the capability. Most items do not clear that bar.

## The discriminating question

For every item type, answer: **what response would a system without this capability give, and what response would one with it give?** If both plausibly produce the same output, the item carries no evidence regardless of how relevant it looks.

## Name the alternative explanations

A wrong answer is evidence about the target capability only if better explanations are ruled out. The usual competitors:

- **Format compliance** — the system had the capability but broke the output contract. An adaptation problem masquerading as a capability measurement.
- **Item difficulty unrelated to the construct** — obscure vocabulary, ambiguous phrasing, an unstated convention.
- **A prerequisite capability** — failing an arithmetic-in-context item may be a reading failure, not an arithmetic one.
- **Contamination** — the item is in training data, so a correct answer is evidence of memorisation.
- **Label error** — the reference answer is wrong. Sample and check before blaming the system.

Write the dominant alternative for each item type into `03_content.md` and say why the item still discriminates.

## Coverage before volume

Capabilities named in Q3 need items each, not items in aggregate. Build the coverage table first and let it size the pool. A pool that is large but concentrated measures one capability precisely and the rest not at all.

Also vary within a capability: if every item for a construct shares a template, the eval measures performance on that template.

## Re-purposed data

Data built for another purpose is the most common shortcut and failure mode 5. Before re-using a dataset, answer: what capability was it built to elicit, how does that differ from yours, and what in its construction makes it still informative? If the honest answer is "it was available," record that as the justification and let the validity register carry the weight.

## Items are a design surface, not a scraping target

Ambiguity found while writing items usually means the capability definition is underspecified. That is a signal to loop back to stage 2, not to resolve the ambiguity silently inside an item.
