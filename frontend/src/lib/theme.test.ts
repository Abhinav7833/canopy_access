import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resolveTheme, setTheme, storedTheme, THEME_KEY, toggleTheme } from "@/lib/theme";

function mockMatchMedia(dark: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: q.includes("dark") ? dark : !dark,
    media: q, addEventListener() {}, removeEventListener() {},
    addListener() {}, removeListener() {}, dispatchEvent() { return false; },
    onchange: null,
  }));
}

describe("theme", () => {
  beforeEach(() => { localStorage.clear(); document.documentElement.removeAttribute("data-theme"); });
  afterEach(() => vi.unstubAllGlobals());

  it("falls back to the system preference when nothing is stored", () => {
    mockMatchMedia(true);
    expect(storedTheme()).toBeNull();
    expect(resolveTheme()).toBe("dark");
  });

  it("prefers the stored choice over the system preference", () => {
    mockMatchMedia(true);
    setTheme("light");
    expect(localStorage.getItem(THEME_KEY)).toBe("light");
    expect(resolveTheme()).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("toggles, persists, and applies the opposite theme", () => {
    mockMatchMedia(false); // system light
    expect(toggleTheme()).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(toggleTheme()).toBe("light");
  });
});
