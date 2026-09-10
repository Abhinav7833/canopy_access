import { Badge } from "@/components/ui/Badge";
import type { RiskTone } from "@/lib/format";

/** What the confidence rating means, and what its risk bands say — honest semantics only
 * (claims that hold up read low; gaps read higher), no invented magnitudes. */
const BANDS: { label: string; tone: RiskTone; meaning: string }[] = [
  { label: "Low", tone: "low", meaning: "The disclosed claims hold up against the satellite record." },
  {
    label: "Medium",
    tone: "medium",
    meaning: "Some claims lag or vary from what was disclosed, worth watching.",
  },
  { label: "High", tone: "high", meaning: "Material gaps between what was promised and what's observed." },
];

export function RatingExplainer() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
        <div className="max-w-2xl">
          <p className="label">What the rating means</p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-ink sm:text-[27px]">
            One number, and the reasons behind it.
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-muted">
            The confidence rating is the single figure a review acts on: how on-track an asset is
            against its own disclosed claims. The risk band sets the tone; the signals behind it are
            always shown.
          </p>
        </div>
        <dl className="mt-10 grid gap-px overflow-hidden rounded-card border border-border bg-border sm:grid-cols-3">
          {BANDS.map((b) => (
            <div key={b.label} className="bg-surface p-5">
              <dt>
                <Badge tone={b.tone}>{b.label} risk</Badge>
              </dt>
              <dd className="mt-3 text-sm leading-relaxed text-muted">{b.meaning}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
