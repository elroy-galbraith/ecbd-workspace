# worksheets — the record library

One folder per run. Both pipelines write here; nothing else does.

## Shape

```
worksheets/
├─ _index/log.md                    the catalog — one line per run
├─ design-<slug>/                   from _templates/design-run/
├─ audit-<slug>/                    from _templates/audit-run/
└─ measure-<slug>/                  from _templates/measure-run/
```

A new run is a **copy of a template**, not a blank page. The template is the schema.

If an **in-progress** record drifts from its template's shape, re-stamp it. **Completed records are never re-stamped** — a finished worksheet records what was asked at the time, and rewriting it to a newer template destroys that. `_templates/CONTEXT.md` states the same rule from the template side.

## Status without a status file

A run's state is `status:` in its `RUN.md` frontmatter (the lifecycle) and the ticks in its "Where this run is" table (which stages are done). Both live in that one file, and every stage contract's closing step updates it. `_index/log.md` says which runs exist; it carries no status.

Because a run folder is copied whole from a template, file *existence* does not signal progress — every file is there from minute one. That is why progress is recorded explicitly rather than derived.

## The lifecycle

This is the authority for these values. `RUN.md` frontmatter carries them and points here.

| Value | Means | Set by |
|---|---|---|
| `intake` | the folder exists, the first stage has not finished | the template, on copy |
| `in-progress` | at least one stage has written its output | every stage's closing step, until a terminal stage moves it on |
| `review` | the worksheet is written and awaiting a human gate | design stage 7's human check; audit stage 6, before the second reader; measure stage 4 |
| `complete` | the final human gate passed | the human check of design stage 8 / audit stage 6 / measure stage 4 — never a Process step, because a gate is a person |
| `archived` | superseded, abandoned, or about a version no longer in use | a person, deliberately — no stage sets this. Say why in the run's title line and leave the record in place; archiving is a label, not a deletion |

**Reopening.** A `complete` run returns to `review` when new evidence arrives — typically from a measure run writing into it. Only a person does that. A measure stage may append evidence and add a loop-back row; moving the run out of `complete` is a gate, and gates are people.

## Records are not version-controlled

`.gitignore` excludes every run folder. Only the scaffold — this file and `_index/log.md` — is committed, because worksheets concern the systems you actually evaluate and often name client work or unreleased models.

Two consequences. A fresh clone gives you a working pipeline and an empty library, which is what you want. And **your runs exist in one place only** — if they matter, they need a backup that is not this repo.

## Reading a record

Read a run folder top to bottom in file-number order and you have the complete worksheet. That property is why files are numbered and why stages write into the record rather than into their own output folders.

## Cross-referencing

Records link to each other by relative path — an audit of an eval designed here cites that design record, and a design run that borrows a capability definition cites where it came from. One home per fact: cite the definition, do not copy it.
