# _templates — the stamps

Blank starters. A new run is a copy of one of these, never a blank page — the template *is* the schema.

| Template | Copy to | Used by |
|---|---|---|
| `design-run/` | `worksheets/design-<slug>/` | `01-design/` |
| `audit-run/` | `worksheets/audit-<slug>/` | `02-audit/` |
| `measure-run/` | `worksheets/measure-<slug>/` | `03-measure/` |

## Changing a template

Templates encode the worksheet's shape, so a change here changes every future record. Two rules:

- **Question wording lives in `_shared/worksheet-questions.md`, not here.** Templates carry section headers and prompts; if the canonical wording changes, the templates point at it rather than restating it.
- **Do not re-stamp completed records.** A finished worksheet is a record of what was asked at the time. Add the new section to in-progress runs only, and note the template change in that run's loop-back table. `worksheets/CONTEXT.md` states the same rule from the record side and is the authority on record shape.
