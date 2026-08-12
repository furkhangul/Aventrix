import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RegisterPage } from "@/pages/register-page";
import { renderWithProviders } from "../test-utils";

describe("RegisterPage", () => {
  it("rejects a weak password before hitting the network", async () => {
    vi.stubGlobal("fetch", vi.fn());
    renderWithProviders(<RegisterPage />, { route: "/register" });

    await userEvent.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await userEvent.type(screen.getByLabelText("Email"), "ada@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "weak");
    await userEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("At least 10 characters")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("accepts a strong password and submits", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({
        id: "1",
        email: "ada@example.com",
        full_name: "Ada Lovelace",
        avatar_url: null,
        role: "USER",
        is_active: true,
        is_email_verified: false,
        is_2fa_enabled: false,
        created_at: new Date().toISOString(),
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<RegisterPage />, { route: "/register" });
    await userEvent.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await userEvent.type(screen.getByLabelText("Email"), "ada@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "StrongPass123");
    await userEvent.click(screen.getByRole("button", { name: "Create account" }));

    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalled());
  });
});
