import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { RunListPage } from "./pages/RunListPage";
import { NewRunPage } from "./pages/NewRunPage";
import { StagePage } from "./pages/StagePage";
import { useRun } from "./api/queries";

function RunRedirect() {
  const { slug } = useParams<{ slug: string }>();
  const run = useRun(slug);

  if (run.isLoading) return <p>Loading run…</p>;
  if (run.isError || !run.data) return <p role="alert">Could not load run '{slug}'.</p>;

  const current = run.data.stages.find((row) => !run.data.approved_stages.includes(row.stage));
  const stage = current?.stage ?? run.data.stages[run.data.stages.length - 1]?.stage ?? "01";
  return <Navigate to={`/runs/${slug}/stages/${stage}`} replace />;
}

function KeyedStagePage() {
  const { slug, stage } = useParams<{ slug: string; stage: string }>();
  return <StagePage key={`${slug}/${stage}`} />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<RunListPage />} />
      <Route path="/runs/new" element={<NewRunPage />} />
      <Route path="/runs/:slug" element={<RunRedirect />} />
      <Route path="/runs/:slug/stages/:stage" element={<KeyedStagePage />} />
    </Routes>
  );
}
