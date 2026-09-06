# setup — one-time factory configuration

One job: turn team-specific answers into `_shared/house-context.md`.

## Inputs
- Working: `questionnaire.md`, answered by a person

## Process
1. Read the answered questionnaire.
2. Write `_shared/house-context.md` under the same seven headings, condensed. Under a page.
3. Where an answer contradicts a default in `_shared/`, do not edit the default — note the divergence in house-context and let the stage contract's reference order resolve it.

## Outputs
- `_shared/house-context.md`

## Human check
Read house-context.md as though you were about to start a run tomorrow. Anything you would not need at a stage boundary is padding — cut it. It costs tokens on nearly every stage load.
