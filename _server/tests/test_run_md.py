import pytest

from app.run_md import RunMdError, add_loop_back, tick_stage, untick_stage

SAMPLE = """# A run

| File | Stage | Questions | Done |
|---|---|---|---|
| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |
| `02_capability.md` | 02 | Q3–Q5 | [ ] |

## Loop-backs

| Date | From stage | Back to stage | What forced it | What changed |
|---|---|---|---|---|
"""


def test_tick_stage_sets_only_the_matching_row():
    result = tick_stage(SAMPLE, "01")
    assert "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [x] |" in result
    assert "| `02_capability.md` | 02 | Q3–Q5 | [ ] |" in result


def test_tick_unknown_stage_raises():
    with pytest.raises(RunMdError):
        tick_stage(SAMPLE, "99")


def test_untick_stage_reverses_a_tick():
    ticked = tick_stage(SAMPLE, "01")
    result = untick_stage(ticked, "01")
    assert "| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |" in result


def test_add_loop_back_appends_a_row():
    result = add_loop_back(
        SAMPLE,
        date="2026-09-09",
        from_stage="07",
        back_to_stage="02",
        forced_by="capability too vague",
        what_changed="tightened the definition",
    )
    assert "| 2026-09-09 | 07 | 02 | capability too vague | tightened the definition |" in result
