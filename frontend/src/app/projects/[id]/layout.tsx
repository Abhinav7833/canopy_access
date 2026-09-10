import Link from "next/link";
import { ProjectHeader } from "@/components/features/ProjectHeader";
import { SectionNav } from "@/components/features/SectionNav";

export default async function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
      <Link
        href="/portfolio"
        className="inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-ink"
      >
        <span aria-hidden>←</span> Portfolio
      </Link>
      <ProjectHeader id={id} />
      <SectionNav id={id} />
      <div className="pt-1">{children}</div>
    </div>
  );
}
