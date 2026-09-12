import { beforeEach, describe, expect, it, vi } from "vitest";
import { clearSessionId, loadPanelCollapsed, loadSessionId, storePanelCollapsed, storeSessionId } from "./sessionStorage";

describe("sessionStorage helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("round-trips a stored session id", () => {
    storeSessionId("design-my-eval", "02", "abc-123");
    expect(loadSessionId("design-my-eval", "02")).toBe("abc-123");
  });

  it("returns null when nothing is stored", () => {
    expect(loadSessionId("design-my-eval", "03")).toBeNull();
  });

  it("clears a stored session id", () => {
    storeSessionId("design-my-eval", "02", "abc-123");
    clearSessionId("design-my-eval", "02");
    expect(loadSessionId("design-my-eval", "02")).toBeNull();
  });

  it("keeps different (runKey, stage) pairs independent", () => {
    storeSessionId("design-my-eval", "01", "session-a");
    storeSessionId("design-my-eval", "02", "session-b");
    expect(loadSessionId("design-my-eval", "01")).toBe("session-a");
    expect(loadSessionId("design-my-eval", "02")).toBe("session-b");
  });

  it("does not throw when localStorage access fails", () => {
    const spy = vi.spyOn(window.localStorage.__proto__, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => storeSessionId("design-my-eval", "01", "x")).not.toThrow();
    spy.mockRestore();
  });
});

describe("panel collapse helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns null when nothing is stored", () => {
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBeNull();
  });

  it("round-trips a stored collapse flag", () => {
    storePanelCollapsed("design-my-eval", "chat", true);
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBe(true);

    storePanelCollapsed("design-my-eval", "chat", false);
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBe(false);
  });

  it("keeps file-tree and chat collapse state independent", () => {
    storePanelCollapsed("design-my-eval", "file-tree", true);
    storePanelCollapsed("design-my-eval", "chat", false);

    expect(loadPanelCollapsed("design-my-eval", "file-tree")).toBe(true);
    expect(loadPanelCollapsed("design-my-eval", "chat")).toBe(false);
  });

  it("does not throw when localStorage access fails", () => {
    const spy = vi.spyOn(window.localStorage.__proto__, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(() => storePanelCollapsed("design-my-eval", "chat", true)).not.toThrow();
    spy.mockRestore();
  });
});
