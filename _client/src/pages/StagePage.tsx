import { useState } from "react";
import { useParams } from "react-router-dom";
import { useRun, useSession, useStageDiff } from "../api/queries";
import { useApproveStage, useRejectStage, useStartStage } from "../api/mutations";
import { StageRail } from "../components/StageRail";
import { RunSwitcher } from "../components/RunSwitcher";
import { DocumentPane } from "../components/DocumentPane";
import { ReviewBanner } from "../components/ReviewBanner";
import { DiffView } from "../components/DiffView";
import { RejectDialog } from "../components/RejectDialog";
import { ChatDrawer } from "../components/ChatDrawer";
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

  return (
    <div className="stage-page">
      <header className="stage-page__header">
        <RunSwitcher currentSlug={slug} />
        <span>
          {run.data.slug} | stage {stage}
        </span>
      </header>
      <div className="stage-page__body">
        <StageRail slug={slug} stages={run.data.stages} approvedStages={run.data.approved_stages} activeStage={stage} />
        <main className="stage-page__document">
          {readyForReview && (
            <ReviewBanner
              onViewDiff={() => setShowDiff(true)}
              onApprove={() => approve.mutate()}
              onReject={() => setShowReject(true)}
              approving={approve.isPending}
            />
          )}
          {showDiff && diff.data && <DiffView diff={diff.data.diff} />}
          {showReject && (
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
          {currentRow && <DocumentPane slug={slug} file={currentRow.file} />}
        </main>
      </div>
      <ChatDrawer
        runKey={slug}
        stage={stage}
        startSession={(brief) => startStage.mutateAsync(brief)}
        onSessionId={setSessionId}
      />
    </div>
  );
}
