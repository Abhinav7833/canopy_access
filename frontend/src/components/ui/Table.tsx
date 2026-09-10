import type { ReactNode } from "react";

const ALIGN = { left: "text-left", right: "text-right", center: "text-center" } as const;
type Align = keyof typeof ALIGN;

export function Table({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`overflow-x-auto rounded-card border border-border bg-surface shadow-card ${className}`}
    >
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  );
}

export function Thead({ children }: { children: ReactNode }) {
  return <thead className="border-b border-border bg-surface-muted">{children}</thead>;
}

export function Th({
  children,
  align = "left",
  className = "",
}: {
  children: ReactNode;
  align?: Align;
  className?: string;
}) {
  return <th className={`label px-4 py-2.5 ${ALIGN[align]} ${className}`}>{children}</th>;
}

export function Tbody({ children }: { children: ReactNode }) {
  return <tbody>{children}</tbody>;
}

export function Td({
  children,
  align = "left",
  className = "",
}: {
  children: ReactNode;
  align?: Align;
  className?: string;
}) {
  return <td className={`px-4 py-3 ${ALIGN[align]} text-ink ${className}`}>{children}</td>;
}
