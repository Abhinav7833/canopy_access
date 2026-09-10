import Link from "next/link";
import { BrandLockup } from "@/components/layout/Brand";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

export function TopBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-6">
        <Link href="/" className="flex shrink-0 items-center" aria-label="Canopy home">
          {/* Above the fold on every route, so it is not lazy-loaded. */}
          <BrandLockup priority />
        </Link>
        <span className="hidden text-faint sm:inline">/</span>
        <span className="hidden text-sm text-muted sm:inline">Evidence &amp; Risk</span>
        <div className="ml-auto flex items-center gap-2">
          <Link
            href="/portfolio"
            className="rounded-md px-2.5 py-1 text-sm text-muted transition-colors hover:text-ink"
          >
            Portfolio
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
