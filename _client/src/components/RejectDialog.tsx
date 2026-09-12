import { useState } from "react";
import { IconAlertTriangle } from "./icons";

interface RejectDialogProps {
  approvedStages: string[];
  currentStage: string;
  onSubmit: (input: { target_stage: string; reason: string }) => void;
  onCancel: () => void;
}

export function RejectDialog({ approvedStages, currentStage, onSubmit, onCancel }: RejectDialogProps) {
  const candidates = approvedStages.filter((stage) => stage !== currentStage);
  const [targetStage, setTargetStage] = useState(candidates[0] ?? "");
  const [reason, setReason] = useState("");

  return (
    <div className="reject-overlay">
      <div role="dialog" aria-label="Reject stage" className="reject-dialog">
        <h2 className="reject-dialog__title">
          <IconAlertTriangle width={18} height={18} />
          Reject stage
        </h2>
        <label className="reject-dialog__field">
          Send back to
          <select value={targetStage} onChange={(event) => setTargetStage(event.target.value)}>
            {candidates.map((stage) => (
              <option key={stage} value={stage}>
                {stage}
              </option>
            ))}
          </select>
        </label>
        <label className="reject-dialog__field">
          Reason
          <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
        </label>
        <div className="reject-dialog__actions">
          <button className="btn btn--ghost" onClick={onCancel}>
            Cancel
          </button>
          <button
            className="btn btn--danger"
            onClick={() => onSubmit({ target_stage: targetStage, reason })}
            disabled={!targetStage || !reason.trim()}
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  );
}
