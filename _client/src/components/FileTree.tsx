import { useState } from "react";
import { Link } from "react-router-dom";
import { useRunTree } from "../api/queries";
import { loadPanelCollapsed, storePanelCollapsed } from "../lib/sessionStorage";
import type { RunTreeNode, StageTableRow } from "../api/types";
import { isStageUnlocked } from "./StageRail";
import { IconFile, IconFolder, IconLock } from "./icons";

interface FileTreeProps {
  slug: string;
  stages: StageTableRow[];
  approvedStages: string[];
  activeStage: string;
  gated: boolean;
}

export function findOwningStage(stages: StageTableRow[], path: string): string | undefined {
  let best: StageTableRow | undefined;
  for (const row of stages) {
    const rowPath = row.file.replace(/\/$/, "");
    if (path !== rowPath && !path.startsWith(`${rowPath}/`)) continue;
    if (!best || rowPath.length > best.file.replace(/\/$/, "").length) {
      best = row;
    }
  }
  return best?.stage;
}

export function FileTree({ slug, stages, approvedStages, activeStage, gated }: FileTreeProps) {
  const tree = useRunTree(slug);
  const [collapsed, setCollapsed] = useState(() => loadPanelCollapsed(slug, "file-tree") ?? false);

  function toggle() {
    setCollapsed((current) => {
      const next = !current;
      storePanelCollapsed(slug, "file-tree", next);
      return next;
    });
  }

  return (
    <nav aria-label="Run files" className={`file-tree${collapsed ? " file-tree--collapsed" : ""}`}>
      <button type="button" className="file-tree__toggle" onClick={toggle}>
        <IconFolder width={14} height={14} />
        {collapsed ? "Expand files" : "Collapse files"}
      </button>
      {!collapsed && (
        <div className="file-tree__nodes">
          {tree.isLoading && <p className="file-tree__notice">Loading files…</p>}
          {tree.isError && <p role="alert">Could not load files.</p>}
          {tree.data?.tree.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              slug={slug}
              stages={stages}
              approvedStages={approvedStages}
              activeStage={activeStage}
              gated={gated}
            />
          ))}
        </div>
      )}
    </nav>
  );
}

interface TreeNodeProps extends FileTreeProps {
  node: RunTreeNode;
}

function TreeNode({ node, slug, stages, approvedStages, activeStage, gated }: TreeNodeProps) {
  if (node.is_dir) {
    return (
      <details className="file-tree__dir" open>
        <summary>
          <IconFolder width={13} height={13} />
          {node.name}
        </summary>
        <div className="file-tree__children">
          {(node.children ?? []).map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              slug={slug}
              stages={stages}
              approvedStages={approvedStages}
              activeStage={activeStage}
              gated={gated}
            />
          ))}
        </div>
      </details>
    );
  }

  const owningStage = findOwningStage(stages, node.path);
  if (owningStage === undefined) {
    return (
      <span className="file-tree__file file-tree__file--inert" aria-disabled="true">
        <IconFile width={13} height={13} />
        {node.name}
      </span>
    );
  }

  const unlocked = gated ? isStageUnlocked(stages, approvedStages, owningStage) : true;
  if (!unlocked) {
    return (
      <span className="file-tree__file file-tree__file--locked" aria-disabled="true">
        <IconLock width={12} height={12} />
        {node.name}
      </span>
    );
  }

  return (
    <Link
      to={`/runs/${slug}/stages/${owningStage}`}
      className={`file-tree__file${owningStage === activeStage ? " file-tree__file--active" : ""}`}
    >
      <IconFile width={13} height={13} />
      {node.name}
    </Link>
  );
}
