"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { EvidenceLauncher } from "@/components/features/EvidenceLauncher";

// The linear disclosure -> confidence narrative (see
// docs/specs/2026-07-13-canopy-disclosure-direction.md). Order matters — it's the story.
const SECTIONS = [
  { slug: "", label: "Disclosure" },
  { slug: "locate", label: "Locate" },
  { slug: "timeline", label: "Observe" },
  { slug: "crosscheck", label: "Cross-check" },
  { slug: "confidence", label: "Confidence" },
  { slug: "ask", label: "Ask" },
  { slug: "memo", label: "Memo" },
];

export function SectionNav({ id }: { id: string }) {
  const path = usePathname();
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border">
      <nav className="flex gap-6">
        {SECTIONS.map((s) => {
          const href = `/projects/${id}${s.slug ? `/${s.slug}` : ""}`;
          const active = path === href;
          return (
            <Link
              key={s.slug}
              href={href}
              className={`-mb-px border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
                active
                  ? "border-accent text-ink"
                  : "border-transparent text-muted hover:text-ink"
              }`}
            >
              {s.label}
            </Link>
          );
        })}
      </nav>
      <EvidenceLauncher id={id} />
    </div>
  );
}
