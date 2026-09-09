import { Link } from "react-router-dom";
import type { StageTableRow } from "../api/types";

interface StageRailProps {
  slug: string;
  stages: StageTableRow[];
  approvedStages: string[];
  activeStage: string;
}

export function isStageUnlocked(stages: StageTableRow[], approvedStages: string[], stage: string): boolean {
  const index = stages.findIndex((s) => s.stage === stage);
  if (index <= 0) return true;
  return stages.slice(0, index).every((s) => approvedStages.includes(s.stage));
}

export function StageRail({ slug, stages, approvedStages, activeStage }: StageRailProps) {
  return (
    <nav aria-label="Stage progress" className="stage-rail">
      {stages.map((row) => {
        const unlocked = isStageUnlocked(stages, approvedStages, row.stage);
        const approved = approvedStages.includes(row.stage);
        const isActive = row.stage === activeStage;
        const label = `${row.stage}${approved ? " ✓" : isActive ? " ●" : ""}`;

        if (!unlocked) {
          return (
            <span key={row.stage} className="stage-rail__item stage-rail__item--locked" aria-disabled="true">
              {label}
            </span>
          );
        }
        return (
          <Link
            key={row.stage}
            to={`/runs/${slug}/stages/${row.stage}`}
            className={`stage-rail__item${isActive ? " stage-rail__item--active" : ""}`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
