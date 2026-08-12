import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NotificationsPage } from "@/pages/notifications-page";
import { renderWithProviders } from "../test-utils";

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: async () => body,
  };
}

describe("NotificationsPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.includes("/notifications/preferences")) {
          return Promise.resolve(jsonResponse({ preferences: {} }));
        }
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                id: "1",
                type: "LINK_FIRST_VISIT",
                title: "First visit received",
                message: "Your link /t/abc123 just received its first visit.",
                data: null,
                is_read: false,
                created_at: new Date().toISOString(),
              },
            ],
            total: 1,
            page: 1,
            page_size: 20,
            unread_count: 1,
          }),
        );
      }),
    );
  });

  it("renders the unread notification and the email-preferences panel", async () => {
    renderWithProviders(<NotificationsPage />, { route: "/notifications" });

    expect(await screen.findByText("First visit received")).toBeInTheDocument();
    expect(screen.getByText("1 unread")).toBeInTheDocument();
    expect(screen.getByText("Email me when…")).toBeInTheDocument();
  });
});
