import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConsentGatePage } from "@/pages/consent-gate-page";
import { renderWithProviders } from "../test-utils";

function renderGate(route: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/t/:code/gate" element={<ConsentGatePage />} />
    </Routes>,
    { route },
  );
}

describe("ConsentGatePage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ needs_password: false, needs_consent: true }),
      }),
    );
  });

  it("shows the consent explanation and Accept/Decline actions", async () => {
    renderGate("/t/abc123/gate");

    expect(await screen.findByText("Before you continue")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Decline" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept & Continue" })).toBeInTheDocument();
  });

  it("does not show a password field when the link doesn't require one", async () => {
    renderGate("/t/abc123/gate");
    await screen.findByText("Before you continue");
    expect(screen.queryByLabelText(/password protected/i)).not.toBeInTheDocument();
  });

  it("shows an unavailable message when the link can't be found", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ error: { message: "NOT_FOUND", code: 404 } }),
      }),
    );
    renderGate("/t/does-not-exist/gate");

    expect(await screen.findByText("This link isn't available")).toBeInTheDocument();
  });
});
