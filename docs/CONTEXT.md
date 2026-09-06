# docs — decisions about the workspace itself

Not part of any run. `worksheets/` holds records of evals; this holds records of choices about the machinery that produces them.

| Folder | What it holds |
|---|---|
| `decisions/` | one file per structural decision: what was chosen, why, what was deferred |

A decision record is written when a choice is made, not when it is implemented. Deferred work is the common case — the record exists so the eventual build has something to check itself against, and so a later reader can tell whether the reasoning still holds.
