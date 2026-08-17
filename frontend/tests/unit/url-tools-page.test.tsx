import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { UrlToolsPage } from "@/pages/url-tools-page";
import { renderWithProviders } from "../test-utils";

describe("UrlToolsPage", () => {
  it("renders all five tool tabs, including QR codes merged in from the old QR page", () => {
    renderWithProviders(<UrlToolsPage />);
    expect(screen.getByRole("tab", { name: "Encode/Decode" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "UTM Builder" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "URL Analyzer" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Redirect Checker" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "QR Code Generator" })).toBeInTheDocument();
  });

  it("encodes and decodes text entirely client-side, with no network calls", async () => {
    renderWithProviders(<UrlToolsPage />);
    await userEvent.type(screen.getByLabelText("Text or URL"), "a b");

    expect(await screen.findByText("a%20b")).toBeInTheDocument();
  });

  it("builds a UTM-tagged URL from the destination and source/medium fields", async () => {
    renderWithProviders(<UrlToolsPage />);
    await userEvent.click(screen.getByRole("tab", { name: "UTM Builder" }));

    await userEvent.type(screen.getByLabelText("Destination URL"), "https://example.com");
    await userEvent.type(screen.getByLabelText("Source"), "instagram");
    await userEvent.type(screen.getByLabelText("Medium"), "social");

    expect(await screen.findByText("https://example.com/?utm_source=instagram&utm_medium=social")).toBeInTheDocument();
  });
});
