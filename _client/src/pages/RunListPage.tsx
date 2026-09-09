import { Link } from "react-router-dom";
import { useRuns } from "../api/queries";
import { IconChevronRight, IconPlus } from "../components/icons";

export function RunListPage() {
  const { data: runs, isLoading, isError } = useRuns();

  if (isLoading) return <p>Loading runs…</p>;
  if (isError) return <p role="alert">Could not load the run list.</p>;

  return (
    <div className="page run-list">
      <header className="page__topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true" />
          ECBD
        </div>
      </header>
      <div className="page__body">
        <div className="page__header">
          <div>
            <h1>Runs</h1>
            <p className="page__sub">Design, audit, and measurement pipelines in this workspace.</p>
          </div>
          <Link to="/runs/new" className="btn btn--primary">
            <IconPlus width={16} height={16} />
            New run
          </Link>
        </div>

        <div className="panel run-list__panel">
          <table>
            <thead>
              <tr>
                <th>Slug</th>
                <th>Mode</th>
                <th>Subject</th>
                <th>Opened</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(runs ?? []).map((run) => (
                <tr key={run.slug}>
                  <td>
                    <Link to={`/runs/${run.slug}`} className="mono">
                      {run.slug}
                    </Link>
                  </td>
                  <td>
                    <span className="tag">{run.mode}</span>
                  </td>
                  <td className="run-list__subject">{run.subject}</td>
                  <td className="mono muted small">{run.opened}</td>
                  <td className="run-list__go">
                    <IconChevronRight width={14} height={14} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
