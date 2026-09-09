interface ReviewBannerProps {
  onViewDiff: () => void;
  onApprove: () => void;
  onReject: () => void;
  approving: boolean;
}

export function ReviewBanner({ onViewDiff, onApprove, onReject, approving }: ReviewBannerProps) {
  return (
    <div role="status" className="review-banner">
      <span>✓ Ready for review — model marked this draft done.</span>
      <button onClick={onViewDiff}>View diff</button>
      <button onClick={onApprove} disabled={approving}>
        {approving ? "Approving…" : "Approve"}
      </button>
      <button onClick={onReject}>Reject…</button>
    </div>
  );
}
