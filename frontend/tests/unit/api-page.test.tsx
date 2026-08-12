import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiPage } from "@/pages/api-page";
import { renderWithProviders } from "../test-utils";

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status < 400,
    status,
    headers: new Headers({ "content-type": "application/json" }),
    json: async () => body,
  };
}

describe("ApiPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, init?: RequestInit) => {
        if (url.includes("/api-keys") && init?.method === "POST") {
          return Promise.resolve(
            jsonResponse(
              {
                id: "key-1",
                name: "CI key",
                key_prefix: "fw_live_abcd1234",
                tier: "FREE",
                is_active: true,
                last_used_at: null,
                created_at: new Date().toISOString(),
                revoked_at: null,
                api_key: "fw_live_secretvalue",
              },
              201,
            ),
          );
        }
        return Promise.resolve(jsonResponse({ items: [], total: 0, page: 1, page_size: 20 }));
      }),
    );
  });

  it("shows the empty state and the tier limits reference", async () => {
    renderWithProviders(<ApiPage />);
    expect(await screen.findByText("No API keys yet")).toBeInTheDocument();
    expect(screen.getByText("100 requests/day")).toBeInTheDocument();
  });

  it("creates a key and reveals the raw secret exactly once", async () => {
    renderWithProviders(<ApiPage />);
    await userEvent.click(await screen.findByRole("button", { name: "New API key" }));
    await userEvent.type(screen.getByLabelText("Name"), "CI key");
    await userEvent.click(screen.getByRole("button", { name: "Create key" }));

    expect(await screen.findByText("fw_live_secretvalue")).toBeInTheDocument();
  });
});
