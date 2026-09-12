import { Link } from "react-router-dom";
import type { StageTableRow } from "../api/types";
import { IconCheck, IconLock } from "./icons";

interface StageRailProps {
  slug: string;
  stages: StageTableRow[];
  approvedStages: string[];
  activeStage: string;
  /** The design pipeline gates each stage behind the last one's approval.
   * Audit and measure runs have no such gate -- every stage is viewable,
   * and "approved" is just each stage's own Done tick. Defaults to true. */
  gated?: boolean;
}

export function isStageUnlocked(stages: StageTableRow[], approvedStages: string[], stage: string): boolean {
  const index = stages.findIndex((s) => s.stage === stage);
  if (index <= 0) return true;
  return stages.slice(0, index).every((s) => approvedStages.includes(s.stage));
}

export function stageName(file: string): string {
  const base = file.replace(/\/$/, "").split("/").pop() ?? file;
  const withoutNumber = base.replace(/^\d+_/, "").replace(/\.[^.]+$/, "");
  return withoutNumber.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

type StageState = "approved" | "active" | "upcoming" | "locked";

export function StageRail({ slug, stages, approvedStages, activeStage, gated = true }: StageRailProps) {
  return (
    <nav aria-label="Stage progress" className="stage-rail">
      {stages.map((row, index) => {
        const unlocked = gated ? isStageUnlocked(stages, approvedStages, row.stage) : true;
        const approved = row.done;
        const isActive = row.stage === activeStage;
        const label = `${row.stage} ${stageName(row.file)}`;
        const state: StageState = approved ? "approved" : isActive ? "active" : unlocked ? "upcoming" : "locked";
        const isLast = index === stages.length - 1;

        const marker = (
          <span className="stage-rail__marker">
            <span className="stage-rail__dot">
              {approved ? <IconCheck width={11} height={11} /> : state === "locked" ? <IconLock width={11} height={11} /> : null}
            </span>
            {!isLast && <span className="stage-rail__connector" />}
          </span>
        );

        if (!unlocked) {
          return (
            <span
              key={row.stage}
              className={`stage-rail__item stage-rail__item--${state}`}
              aria-disabled="true"
              aria-label={row.stage}
            >
              {marker}
              {label}
            </span>
          );
        }
        return (
          <Link
            key={row.stage}
            to={`/runs/${slug}/stages/${row.stage}`}
            className={`stage-rail__item stage-rail__item--${state}`}
            aria-label={row.stage}
          >
            {marker}
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
