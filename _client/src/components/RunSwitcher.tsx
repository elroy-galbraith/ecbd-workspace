import { useNavigate } from "react-router-dom";
import { useRuns } from "../api/queries";

interface RunSwitcherProps {
  currentSlug: string;
}

export function RunSwitcher({ currentSlug }: RunSwitcherProps) {
  const { data: runs } = useRuns();
  const navigate = useNavigate();

  return (
    <select
      aria-label="Switch run"
      defaultValue={currentSlug}
      onChange={(event) => navigate(`/runs/${event.target.value}`)}
    >
      {(runs ?? []).map((run) => (
        <option key={run.slug} value={run.slug}>
          {run.subject || run.slug}
        </option>
      ))}
    </select>
  );
}
