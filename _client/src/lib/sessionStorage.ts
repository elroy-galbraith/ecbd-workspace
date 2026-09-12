const PREFIX = "ecbd-session:";

function key(runKey: string, stage: string): string {
  return `${PREFIX}${runKey}:${stage}`;
}

export function storeSessionId(runKey: string, stage: string, sessionId: string): void {
  try {
    window.localStorage.setItem(key(runKey, stage), sessionId);
  } catch {
    // localStorage unavailable (private mode, disabled) -- the session just won't survive a refresh
  }
}

export function loadSessionId(runKey: string, stage: string): string | null {
  try {
    return window.localStorage.getItem(key(runKey, stage));
  } catch {
    return null;
  }
}

export function clearSessionId(runKey: string, stage: string): void {
  try {
    window.localStorage.removeItem(key(runKey, stage));
  } catch {
    // ignore
  }
}

export type PanelKey = "file-tree" | "chat";

function collapseKey(runKey: string, panel: PanelKey): string {
  return `ecbd-collapse:${panel}:${runKey}`;
}

export function loadPanelCollapsed(runKey: string, panel: PanelKey): boolean | null {
  try {
    const raw = window.localStorage.getItem(collapseKey(runKey, panel));
    return raw === null ? null : raw === "true";
  } catch {
    return null;
  }
}

export function storePanelCollapsed(runKey: string, panel: PanelKey, collapsed: boolean): void {
  try {
    window.localStorage.setItem(collapseKey(runKey, panel), String(collapsed));
  } catch {
    // localStorage unavailable -- the collapse state just won't survive a refresh
  }
}
