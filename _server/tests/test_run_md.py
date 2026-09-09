import pytest

from app.run_md import (
    RunMdError,
    add_approved_stage,
    add_loop_back,
    get_approved_stages,
    remove_approved_stages,
    tick_stage,
    untick_stage,
)

SAMPLE = """# A run

| File | Stage | Questions | Done |
|---|---|---|---|
| `01_intended-use.md` | 01 | Framing, Q1–Q2 | [ ] |
| `02_capability.md` | 02 | Q3–Q5 | [ ] |

## Loop-backs

| Date | From stage | Back to stage | What forced it | What changed |
|---|---|---|---|---|
"""

FRONTMATTER_SAMPLE = """---
slug: design-my-eval
status: intake          # lifecycle values and their meaning: worksheets/CONTEXT.md
objects_of_evaluation: []
capabilities: []
approved_stages: []
opened: 2026-09-09
closed:
owner:
---

# A run

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


def test_get_approved_stages_empty_list():
    assert get_approved_stages(FRONTMATTER_SAMPLE) == []


def test_get_approved_stages_parses_quoted_values():
    text = FRONTMATTER_SAMPLE.replace('approved_stages: []', 'approved_stages: ["01", "02"]')
    assert get_approved_stages(text) == ["01", "02"]


def test_get_approved_stages_missing_line_raises():
    with pytest.raises(RunMdError):
        get_approved_stages(SAMPLE)


def test_add_approved_stage_adds_to_empty_list():
    result = add_approved_stage(FRONTMATTER_SAMPLE, "01")
    assert get_approved_stages(result) == ["01"]


def test_add_approved_stage_appends_to_existing_list():
    text = FRONTMATTER_SAMPLE.replace('approved_stages: []', 'approved_stages: ["01"]')
    result = add_approved_stage(text, "02")
    assert get_approved_stages(result) == ["01", "02"]


def test_add_approved_stage_is_idempotent():
    text = FRONTMATTER_SAMPLE.replace('approved_stages: []', 'approved_stages: ["01"]')
    result = add_approved_stage(text, "01")
    assert get_approved_stages(result) == ["01"]


def test_add_approved_stage_raises_if_no_line_found():
    with pytest.raises(RunMdError):
        add_approved_stage(SAMPLE, "01")


def test_remove_approved_stages_removes_listed_stages():
    text = FRONTMATTER_SAMPLE.replace('approved_stages: []', 'approved_stages: ["01", "02", "03"]')
    result = remove_approved_stages(text, ["01", "03"])
    assert get_approved_stages(result) == ["02"]


def test_remove_approved_stages_is_idempotent_for_absent_stages():
    text = FRONTMATTER_SAMPLE.replace('approved_stages: []', 'approved_stages: ["01"]')
    result = remove_approved_stages(text, ["01", "99"])
    assert get_approved_stages(result) == []


def test_remove_approved_stages_raises_if_no_line_found():
    with pytest.raises(RunMdError):
        remove_approved_stages(SAMPLE, ["01"])
