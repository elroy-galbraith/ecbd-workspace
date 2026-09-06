# 04_adaptation — specify how objects are instructed

One job: fix how every object of evaluation is prompted, configured, or adapted, so results are comparable and no object is disadvantaged.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `03_content.md` from the run folder
- Working (this run): `02_capability.md` from the run folder
- Working (this run): `01_intended-use.md` from the run folder — Q10 is answered against every object named in Q1
- Reference (every run): ../../_shared/worksheet-questions.md (Q9–Q11)
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (if it exists): ../../_shared/house-context.md

## Process
1. Specify the full path from item to response: prompt template, system message, few-shot examples and their selection, decoding parameters, tool access, retries, output format and parser.
2. Prescribe it. Leaving adaptation to the user makes results incomparable across users — failure mode 6, checked at stage 7. If some choice must stay open, say which, and require users to report what they used.
3. Answer Q10 against *every* intended object of evaluation from Q1, not the one you developed against. Name any object the method disadvantages — a format-sensitive model, one with a different context window, one without tool support.
4. State what a poor score would mean: lacking the capability, or failing to comply with the format. If those two cannot be distinguished, the design is confounded — fix it here.
5. Answer Q11 with a strength label. Sensitivity checks across prompt variants are the cheapest real evidence available at this stage.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `04_adaptation.md` → the run folder
- prompt templates and config → the run folder's `build/adaptation/`

## Human check
Send one item through the specified adaptation by hand, to two different objects of evaluation. Confirm two things. The parser accepts both responses. And the format neither helps nor hinders either object. Edit this file directly.
