/** Circumference of a circle of the given radius. */
export function circumference(radius: number): number {
  return 2 * Math.PI * radius;
}

/** `stroke-dashoffset` to fill a circular gauge of `radius` to `pct`% (0-100).
 * 0 offset = full; full circumference = empty. Null/out-of-range clamp sensibly. */
export function arcOffset(pct: number | null, radius: number): number {
  const clamped = Math.max(0, Math.min(100, pct ?? 0));
  return circumference(radius) * (1 - clamped / 100);
}
