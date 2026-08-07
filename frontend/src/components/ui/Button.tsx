import type { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'danger';

const VARIANTS: Record<Variant, string> = {
  primary:
    'text-white shadow-sm disabled:opacity-60 disabled:shadow-none ' +
    'bg-[linear-gradient(135deg,rgba(124,58,237,1)_0%,rgba(6,182,212,1)_55%,rgba(249,115,22,0.95)_100%)] ' +
    'hover:brightness-[1.05] active:brightness-[0.98]',
  secondary:
    'text-white/85 border border-white/15 bg-white/5 shadow-sm ' +
    'hover:bg-white/8 hover:border-white/20 active:bg-white/6 disabled:opacity-50',
  danger:
    'text-white shadow-sm disabled:opacity-60 disabled:shadow-none ' +
    'bg-[linear-gradient(135deg,rgba(244,63,94,1)_0%,rgba(251,113,133,0.95)_100%)] ' +
    'hover:brightness-[1.05] active:brightness-[0.98]',
};

// PUBLIC_INTERFACE
export function Button({
  variant = 'primary',
  loading = false,
  children,
  className = '',
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  loading?: boolean;
}) {
  /**
   * Shared button with variants and a busy state.
   *
   * @param variant Visual style (primary, secondary, danger).
   * @param loading When true the button is disabled and marked busy.
   */
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={[
        'inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold',
        'transition duration-150 disabled:cursor-not-allowed',
        'ring-1 ring-white/10',
        'hover:-translate-y-[1px] active:translate-y-0',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/70 focus-visible:ring-offset-0',
        VARIANTS[variant],
        className,
      ].join(' ')}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/50 border-t-white"
        />
      )}
      {children}
    </button>
  );
}
