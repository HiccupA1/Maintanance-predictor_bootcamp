/**
 * Validation for post-login redirect targets (`?next=` / `location.state.from`).
 *
 * Only same-origin, app-relative paths are allowed. Browsers normalise `\` to
 * `/` in URLs, so `/\evil.com` is treated as the protocol-relative
 * `//evil.com`. React Router < 7.18 does not guard against this
 * (GHSA open-redirect via backslash), so the check lives here.
 */

const ORIGIN_PROBE = 'https://app.invalid';

// PUBLIC_INTERFACE
export function safeNextPath(raw: string | null | undefined): string | null {
  /** Return `raw` if it is a safe in-app path, otherwise `null`. */
  if (!raw || raw.length > 2048) return null;
  if (!raw.startsWith('/') || raw.startsWith('//')) return null;
  // Backslashes and control characters (incl. tab/CR/LF, which browsers
  // strip) can turn a relative path into a cross-origin URL.
  // eslint-disable-next-line no-control-regex
  if (/[\\\u0000-\u001f\u007f]/.test(raw)) return null;

  try {
    const url = new URL(raw, ORIGIN_PROBE);
    if (url.origin !== ORIGIN_PROBE) return null;
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return null;
  }
}
