"""The one privileged tool that may create a new run folder. Offered to a
stage's model conversation only when its contract declares bootstrap: true.
Only 'design' is supported until 02-audit and 03-measure get the same
frontmatter treatment as 01-design (Task 3)."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

from . import log_index

_PIPELINE_TEMPLATES = {"design": "design-run"}


class CreateRunError(Exception):
    pass


def create_run(repo_root: Path, pipeline: str, slug: str, subject: str) -> Path:
    if pipeline not in _PIPELINE_TEMPLATES:
        raise CreateRunError(f"pipeline '{pipeline}' is not supported yet")

    full_slug = slug if slug.startswith(f"{pipeline}-") else f"{pipeline}-{slug}"
    run_root = repo_root / "worksheets" / full_slug
    if run_root.exists():
        raise CreateRunError(f"a run named '{full_slug}' already exists")

    template_root = repo_root / "_templates" / _PIPELINE_TEMPLATES[pipeline]
    if not template_root.exists():
        raise CreateRunError(f"template folder missing: {template_root}")
    shutil.copytree(template_root, run_root)

    try:
        opened = date.today().isoformat()
        run_md_path = run_root / "RUN.md"
        text = run_md_path.read_text(encoding="utf-8")
        text = text.replace(f"slug: {pipeline}-<kebab-slug>", f"slug: {full_slug}", 1)
        text = text.replace("opened: YYYY-MM-DD", f"opened: {opened}", 1)
        run_md_path.write_text(text, encoding="utf-8")

        log_index.append_run(repo_root, full_slug, pipeline, subject, opened)
        log_index.commit_log_index(repo_root, full_slug)
    except Exception:
        # Best-effort cleanup: remove the partially-created run folder on any post-copy failure.
        # This prevents the slug from becoming permanently "blocked" on transient errors.
        # Residual risk: a failure during the log-index step may leave an uncommitted change
        # to worksheets/_index/log.md (this cleanup does not attempt to revert that).
        shutil.rmtree(run_root, ignore_errors=True)
        raise

    return run_root
