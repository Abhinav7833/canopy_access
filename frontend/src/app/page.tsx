import Link from "next/link";
import { BrandIcon } from "@/components/layout/Brand";
import { EvidencePipeline } from "@/components/features/EvidencePipeline";
import { RatingExplainer } from "@/components/features/RatingExplainer";
import { TrustBand } from "@/components/features/TrustBand";

/** Marketing landing (the front door): the hero, the evidence-pipeline "how it works" strip, the
 * rating explainer, the methodology band, a closing CTA, and a footer. */
export default function Landing() {
  return (
    <main>
      <section className="mx-auto max-w-4xl px-6 py-24 text-center sm:py-32">
        <p className="label">Green-finance evidence</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          Every financed claim, checked against the satellite record.
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted">
          Canopy turns a green-bond disclosure into a located asset, tracked over time and
          cross-checked against what was promised, then resolved to one explained confidence rating
          with every figure traced to its evidence.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link
            href="/portfolio"
            className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-accent-ink transition-colors hover:bg-accent-hover"
          >
            View the portfolio
          </Link>
        </div>
        <p className="mt-6 text-sm text-muted">
          Independent satellite evidence · every figure cited · one explained rating.
        </p>
      </section>

      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
          <div className="max-w-2xl">
            <p className="label">How it works</p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-ink sm:text-[27px]">
              From a disclosure to one explained rating.
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted">
              Five steps turn a financed green-bond claim into evidence a reviewer can act on, each
              one traceable to the step before it.
            </p>
          </div>
          <EvidencePipeline className="mt-14" />
        </div>
      </section>

      <RatingExplainer />

      <TrustBand />

      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-20 text-center sm:py-24">
          <h2 className="text-2xl font-semibold tracking-tight text-ink sm:text-[27px]">
            See the evidence for yourself.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-muted">
            A set of financed green assets, each taken from disclosure to an explained rating, with
            every figure traceable to its evidence.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              href="/portfolio"
              className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-accent-ink transition-colors hover:bg-accent-hover"
            >
              View the portfolio
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl items-center gap-2.5 px-6 py-8 text-sm text-muted">
          <BrandIcon className="h-5 w-5 shrink-0" />
          <p>Canopy. Disclosure-anchored evidence for green-finance claims.</p>
        </div>
      </footer>
    </main>
  );
}
