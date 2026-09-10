import Image from "next/image";

/** Brand artwork. Each mark ships as two files because the wordmark colour and the mark's
 * green are tuned per background — neither can be recoloured from the other — so both are
 * rendered and the theme shows one (see .brand-on-* in globals.css).
 *
 * `alt=""` throughout: these are decorative wherever they appear, and the surrounding link
 * or text already carries the accessible name. */
type Props = { className?: string; priority?: boolean };

function Pair({
  light,
  dark,
  width,
  height,
  className,
  priority,
}: Props & { light: string; dark: string; width: number; height: number }) {
  const common = { width, height, priority };
  return (
    <>
      {/* shrink-0 + object-contain: in a flex row the image would otherwise be allowed to
          shrink while `h-*` holds the height fixed, which stretches the artwork instead of
          scaling it. Both are needed — one stops the shrink, the other guarantees the
          aspect ratio survives whatever box it ends up in. */}
      <Image
        {...common}
        alt=""
        src={light}
        className={`brand-on-light shrink-0 object-contain ${className ?? ""}`}
      />
      <Image
        {...common}
        alt=""
        src={dark}
        className={`brand-on-dark shrink-0 object-contain ${className ?? ""}`}
      />
    </>
  );
}

/** Mark + wordmark, for the header and anywhere the product is named visually. */
export function BrandLockup({ className = "h-8 w-auto", priority }: Props) {
  return (
    <Pair
      light="/brand/canopy-lockup-on-light.png"
      dark="/brand/canopy-lockup-on-dark.png"
      width={1668}
      height={379}
      className={className}
      priority={priority}
    />
  );
}

/** Mark only, for places where the name is already in the adjacent copy. */
export function BrandIcon({ className = "h-5 w-5", priority }: Props) {
  return (
    <Pair
      light="/brand/canopy-icon-on-light.png"
      dark="/brand/canopy-icon-on-dark.png"
      width={396}
      height={396}
      className={className}
      priority={priority}
    />
  );
}
