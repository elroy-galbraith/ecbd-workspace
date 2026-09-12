import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRuns } from "../api/queries";
import { IconChevronDown } from "./icons";

interface RunSwitcherProps {
  currentSlug: string;
}

export function RunSwitcher({ currentSlug }: RunSwitcherProps) {
  const { data: runs } = useRuns();
  const navigate = useNavigate();
  const [selected, setSelected] = useState(currentSlug);

  useEffect(() => {
    setSelected(currentSlug);
  }, [currentSlug]);

  return (
    <div className="run-switch-wrap">
      <select
        aria-label="Switch run"
        className="run-switch"
        value={selected}
        onChange={(event) => {
          setSelected(event.target.value);
          navigate(`/runs/${event.target.value}`);
        }}
      >
        {(runs ?? []).map((run) => (
          <option key={run.slug} value={run.slug}>
            {run.subject || run.slug}
          </option>
        ))}
      </select>
      <IconChevronDown width={12} height={12} className="run-switch-wrap__chevron" />
    </div>
  );
}
