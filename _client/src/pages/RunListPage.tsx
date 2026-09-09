import { Link } from "react-router-dom";
import { useRuns } from "../api/queries";

export function RunListPage() {
  const { data: runs, isLoading, isError } = useRuns();

  if (isLoading) return <p>Loading runs…</p>;
  if (isError) return <p role="alert">Could not load the run list.</p>;

  return (
    <div className="run-list">
      <h1>Runs</h1>
      <Link to="/runs/new">New run</Link>
      <table>
        <thead>
          <tr>
            <th>Slug</th>
            <th>Mode</th>
            <th>Subject</th>
            <th>Opened</th>
          </tr>
        </thead>
        <tbody>
          {(runs ?? []).map((run) => (
            <tr key={run.slug}>
              <td>
                <Link to={`/runs/${run.slug}`}>{run.slug}</Link>
              </td>
              <td>{run.mode}</td>
              <td>{run.subject}</td>
              <td>{run.opened}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
