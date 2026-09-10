"use client";
import { useEffect, useState } from "react";
import { resolveTheme, toggleTheme, type Theme } from "@/lib/theme";

export function ThemeToggle() {
  // Start "light" for a deterministic SSR render; sync to the real theme after mount
  // (the pre-hydration script has already set the correct <html data-theme>).
  const [theme, setThemeState] = useState<Theme>("light");
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setThemeState(resolveTheme()), []);

  const dark = theme === "dark";
  return (
    <button
      type="button"
      onClick={() => setThemeState(toggleTheme())}
      aria-label={`Switch to ${dark ? "light" : "dark"} theme`}
      title="Toggle theme"
      className="grid h-8 w-8 place-items-center rounded-lg border border-border-strong bg-surface text-muted transition-colors hover:border-faint hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-1 focus-visible:ring-offset-canvas"
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        {dark ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19" />
          </>
        ) : (
          <path d="M20 14.5A7.5 7.5 0 1 1 9.5 4a6 6 0 0 0 10.5 10.5z" />
        )}
      </svg>
    </button>
  );
}
