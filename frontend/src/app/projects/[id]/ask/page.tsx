"use client";
import { use } from "react";
import { AskPanel } from "@/components/features/AskPanel";

export default function Ask({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <div className="space-y-6">
      <AskPanel id={id} />
    </div>
  );
}
