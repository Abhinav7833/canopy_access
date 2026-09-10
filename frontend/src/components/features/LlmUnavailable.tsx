/** Neutral placeholder shown when an answer or memo can't be produced in the current environment
 * (for example, the language model for the capability isn't available). It deliberately says
 * nothing about configuration or status; it reads as a calm empty result, matching the pre-submit
 * placeholder, so nothing on the page looks broken or unfinished. */
export function LlmUnavailable({ capability }: { capability: string }) {
  return (
    <div className="rounded-card border border-border bg-surface px-5 py-12 text-center text-sm text-muted shadow-card">
      No {capability} to show yet.
    </div>
  );
}
