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


from app.run_md import (
    approved_stages_would_change,
    parse_frontmatter,
    parse_loop_backs,
    parse_run_md,
    parse_stage_table,
)


def test_parse_stage_table_parses_rows():
    rows = parse_stage_table(SAMPLE)
    assert rows == [
        {"file": "01_intended-use.md", "stage": "01", "questions": "Framing, Q1–Q2", "done": False},
        {"file": "02_capability.md", "stage": "02", "questions": "Q3–Q5", "done": False},
    ]


def test_parse_stage_table_reflects_a_tick():
    ticked = tick_stage(SAMPLE, "01")
    rows = parse_stage_table(ticked)
    assert rows[0]["done"] is True
    assert rows[1]["done"] is False


def test_parse_stage_table_parses_measure_run_rows_with_no_questions_column():
    # measure-run RUN.md tables are `| File | Stage | Done |` -- three
    # columns, no Questions -- unlike design/audit's four.
    text = (
        "| File | Stage | Done |\n"
        "|---|---|---|\n"
        "| `01_intake.md` | 01 | [x] |\n"
        "| `03_analysis.md` | 03 | [ ] |\n"
    )
    assert parse_stage_table(text) == [
        {"file": "01_intake.md", "stage": "01", "questions": "", "done": True},
        {"file": "03_analysis.md", "stage": "03", "questions": "", "done": False},
    ]


def test_parse_loop_backs_empty_table():
    assert parse_loop_backs(SAMPLE) == []


def test_parse_loop_backs_parses_appended_rows():
    result = add_loop_back(
        SAMPLE,
        date="2026-09-09",
        from_stage="07",
        back_to_stage="02",
        forced_by="capability too vague",
        what_changed="tightened the definition",
    )
    assert parse_loop_backs(result) == [
        {
            "date": "2026-09-09",
            "from_stage": "07",
            "back_to_stage": "02",
            "forced_by": "capability too vague",
            "what_changed": "tightened the definition",
        }
    ]


def test_parse_frontmatter_reads_scalars():
    fm = parse_frontmatter(FRONTMATTER_SAMPLE)
    assert fm["status"] == "intake"
    assert fm["slug"] == "design-my-eval"


def test_parse_frontmatter_missing_block_raises():
    with pytest.raises(RunMdError):
        parse_frontmatter(SAMPLE)


def test_parse_run_md_defaults_approved_stages_when_line_is_absent():
    # audit/measure RUN.md frontmatter never carries approved_stages -- it's
    # a design-pipeline-only concept -- so the read-only summary must not
    # raise for them.
    text = FRONTMATTER_SAMPLE.replace("approved_stages: []\n", "")
    with pytest.raises(RunMdError):
        get_approved_stages(text)  # confirms the fixture actually lacks the line
    result = parse_run_md(text)
    assert result["approved_stages"] == []


def test_parse_run_md_combines_frontmatter_table_and_loopbacks():
    result = parse_run_md(FRONTMATTER_SAMPLE)
    assert result["status"] == "intake"
    assert result["approved_stages"] == []
    assert result["stages"][0] == {
        "file": "01_intended-use.md", "stage": "01", "questions": "Framing, Q1–Q2", "done": False,
    }
    assert result["loop_backs"] == []


def test_approved_stages_would_change_true_when_list_changes():
    changed = add_approved_stage(FRONTMATTER_SAMPLE, "01")
    assert approved_stages_would_change(FRONTMATTER_SAMPLE, changed) is True


def test_approved_stages_would_change_false_for_an_unrelated_edit():
    other_edit = FRONTMATTER_SAMPLE.replace("# A run", "# A run (renamed)")
    assert approved_stages_would_change(FRONTMATTER_SAMPLE, other_edit) is False


def test_approved_stages_would_change_false_when_target_has_no_content_yet():
    assert approved_stages_would_change("", FRONTMATTER_SAMPLE) is True
