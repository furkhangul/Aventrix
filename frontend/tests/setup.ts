import "@testing-library/jest-dom/vitest";
import "@/lib/i18n";

// jsdom doesn't implement matchMedia — ThemeProvider (system theme
// detection) needs it, so every test that mounts the app tree does too.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as unknown as MediaQueryList;
}

