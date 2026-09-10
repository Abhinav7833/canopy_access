/** The methodology / trust band: three honest pillars describing how the evidence holds up. No
 * fabricated trust signals (no customer logos, testimonials, or compliance badges) — credibility
 * comes from describing the real method (Sentinel + disclosure, the trace system, one rating). */
const PILLARS = [
  {
    title: "Independent evidence",
    body: "Every check runs against Sentinel satellite imagery and the disclosure document itself, not the issuer's own reporting.",
  },
  {
    title: "Everything cited",
    body: "Figures carry a trace back to their source, so a number can be followed to the evidence behind it.",
  },
  {
    title: "One explained rating",
    body: "The asset resolves to a single confidence rating with the signals that produced it shown: a number you can interrogate, not a black box.",
  },
];

export function TrustBand() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
        <div className="max-w-2xl">
          <p className="label">How the evidence holds up</p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-ink sm:text-[27px]">
            Credibility you can check, not take on faith.
          </h2>
        </div>
        <div className="mt-10 grid gap-8 sm:grid-cols-3">
          {PILLARS.map((p) => (
            <div key={p.title} className="border-t-2 border-accent-border pt-5">
              <h3 className="text-[15px] font-medium text-ink">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
