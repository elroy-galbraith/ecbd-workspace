import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useRun, useSession, useStageDiff } from "../api/queries";
import { useApproveStage, useRejectStage, useStartStage } from "../api/mutations";
import { StageRail } from "../components/StageRail";
import { RunSwitcher } from "../components/RunSwitcher";
import { DocumentPane } from "../components/DocumentPane";
import { ReviewBanner } from "../components/ReviewBanner";
import { DiffView } from "../components/DiffView";
import { RejectDialog } from "../components/RejectDialog";
import { ChatDrawer } from "../components/ChatDrawer";
import { IconPlus } from "../components/icons";
import { clearSessionId, loadSessionId } from "../lib/sessionStorage";

export function StagePage() {
  const { slug, stage } = useParams<{ slug: string; stage: string }>();
  const [showDiff, setShowDiff] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(() =>
    slug && stage ? loadSessionId(slug, stage) : null,
  );

  const run = useRun(slug);
  const startStage = useStartStage(slug ?? "", stage ?? "");
  const approve = useApproveStage(slug ?? "", stage ?? "");
  const reject = useRejectStage(slug ?? "", stage ?? "");

  const session = useSession(sessionId ?? undefined);
  const diff = useStageDiff(showDiff ? slug : undefined, showDiff ? stage : undefined);

  if (!slug || !stage) return null;
  if (run.isLoading) return <p>Loading run…</p>;
  if (run.isError || !run.data) return <p role="alert">Could not load run '{slug}'.</p>;

  const currentRow = run.data.stages.find((row) => row.stage === stage);
  const readyForReview = session.data?.ready_for_review ?? false;
  const stageOrder = run.data.stages.map((row) => row.stage);
  // Chat, approve/reject, and diff are design-pipeline-only: the backend's
  // stage contracts and gating are hardcoded to it, and audit/measure runs
  // never carry approved_stages to gate against in the first place.
  const isDesign = run.data.mode === "design";

  return (
    <div className="stage-page">
      <header className="stage-page__header">
        <Link to="/" className="brand">
          <span className="brand__mark" aria-hidden="true" />
          ECBD
        </Link>
        <div className="stage-page__divider" aria-hidden="true" />
        <div className="crumb">
          <RunSwitcher currentSlug={slug} />
          <span className="crumb__sep" aria-hidden="true">/</span>
          <span className="crumb__stage mono">stage {stage}</span>
        </div>
        <Link to="/runs/new" className="btn btn--ghost stage-page__new-run">
          <IconPlus width={14} height={14} />
          New run
        </Link>
      </header>
      <div className="stage-page__body">
        <StageRail
          slug={slug}
          stages={run.data.stages}
          approvedStages={run.data.approved_stages}
          activeStage={stage}
          gated={isDesign}
        />
        <main className="stage-page__document">
          {isDesign && readyForReview && (
            <ReviewBanner
              onViewDiff={() => setShowDiff(true)}
              onApprove={() => approve.mutate()}
              onReject={() => setShowReject(true)}
              approving={approve.isPending}
            />
          )}
          {isDesign && showDiff && diff.data && <DiffView diff={diff.data.diff} />}
          {currentRow && <DocumentPane slug={slug} file={currentRow.file} />}
          {isDesign && showReject && (
            <RejectDialog
              approvedStages={run.data.approved_stages}
              currentStage={stage}
              onSubmit={(input) =>
                reject.mutate(input, {
                  onSuccess: () => {
                    setShowReject(false);
                    const targetIndex = stageOrder.indexOf(input.target_stage);
                    const currentIndex = stageOrder.indexOf(stage);
                    if (targetIndex !== -1 && currentIndex !== -1) {
                      for (const s of stageOrder.slice(targetIndex, currentIndex + 1)) {
                        clearSessionId(slug, s);
                      }
                    }
                  },
                })
              }
              onCancel={() => setShowReject(false)}
            />
          )}
        </main>
      </div>
      {isDesign && (
        <ChatDrawer
          runKey={slug}
          stage={stage}
          startSession={(brief) => startStage.mutateAsync(brief)}
          onSessionId={setSessionId}
        />
      )}
    </div>
  );
}
