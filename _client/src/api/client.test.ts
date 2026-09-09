import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./client";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on success", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ hello: "world" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await api.get<{ hello: string }>("/runs");
    expect(result).toEqual({ hello: "world" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/runs"),
      expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "application/json" }) }),
    );
  });

  it("throws ApiError with the status and body text on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      text: async () => "run 'x' does not exist",
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.get("/runs/x")).rejects.toMatchObject(
      new ApiError(404, "run 'x' does not exist"),
    );
  });

  it("sends a JSON body for post", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);

    await api.post("/runs/design/start", { brief: "hi" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/runs/design/start"),
      expect.objectContaining({ method: "POST", body: JSON.stringify({ brief: "hi" }) }),
    );
  });
});
