import type { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'danger';

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-600/50',
  secondary:
    'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:text-slate-400',
  danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-600/50',
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
      className={`inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
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
