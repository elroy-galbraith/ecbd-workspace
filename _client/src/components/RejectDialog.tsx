import { useState } from "react";

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
    <div role="dialog" aria-label="Reject stage">
      <label>
        Send back to
        <select value={targetStage} onChange={(event) => setTargetStage(event.target.value)}>
          {candidates.map((stage) => (
            <option key={stage} value={stage}>
              {stage}
            </option>
          ))}
        </select>
      </label>
      <label>
        Reason
        <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
      </label>
      <button
        onClick={() => onSubmit({ target_stage: targetStage, reason })}
        disabled={!targetStage || !reason.trim()}
      >
        Reject
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  );
}
