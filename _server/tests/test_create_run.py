import pytest

from app.create_run import CreateRunError, create_run


def test_creates_run_folder_from_template(tmp_repo):
    run_root = create_run(tmp_repo, "design", "my-eval", "A test eval")
    assert run_root == tmp_repo / "worksheets" / "design-my-eval"
    assert (run_root / "RUN.md").exists()
    assert (run_root / "01_intended-use.md").exists()


def test_stamps_slug_and_opened_date_into_run_md(tmp_repo):
    run_root = create_run(tmp_repo, "design", "my-eval", "A test eval")
    run_md = (run_root / "RUN.md").read_text(encoding="utf-8")
    assert "slug: design-my-eval" in run_md
    assert "slug: design-<kebab-slug>" not in run_md
    assert "opened: YYYY-MM-DD" not in run_md


def test_records_the_run_in_the_log_index(tmp_repo):
    create_run(tmp_repo, "design", "my-eval", "A test eval")
    log_text = (tmp_repo / "worksheets" / "_index" / "log.md").read_text(encoding="utf-8")
    assert "| design-my-eval | design | A test eval |" in log_text


def test_colliding_slug_raises(tmp_repo):
    create_run(tmp_repo, "design", "my-eval", "A test eval")
    with pytest.raises(CreateRunError):
        create_run(tmp_repo, "design", "my-eval", "A different eval")


def test_unsupported_pipeline_raises(tmp_repo):
    with pytest.raises(CreateRunError):
        create_run(tmp_repo, "audit", "my-eval", "A test eval")
