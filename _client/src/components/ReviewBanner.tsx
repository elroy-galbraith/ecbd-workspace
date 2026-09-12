import { IconCheckCircle, IconColumns } from "./icons";

interface ReviewBannerProps {
  onViewDiff: () => void;
  onApprove: () => void;
  onReject: () => void;
  approving: boolean;
}

export function ReviewBanner({ onViewDiff, onApprove, onReject, approving }: ReviewBannerProps) {
  return (
    <div role="status" className="review-banner">
      <IconCheckCircle width={18} height={18} className="review-banner__icon" />
      <span className="review-banner__text">Ready for review — model marked this draft done.</span>
      <div className="review-banner__actions">
        <button className="btn btn--ghost btn--sm" onClick={onViewDiff}>
          <IconColumns width={13} height={13} />
          View diff
        </button>
        <button className="btn btn--primary btn--sm" onClick={onApprove} disabled={approving}>
          {approving ? "Approving…" : "Approve"}
        </button>
        <button className="btn btn--danger-ghost btn--sm" onClick={onReject}>
          Reject…
        </button>
      </div>
    </div>
  );
}
