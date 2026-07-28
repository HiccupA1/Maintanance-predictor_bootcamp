/** Presentation helpers shared by screens (no business logic). */

// PUBLIC_INTERFACE
export function formatDateTime(value?: string | null): string {
  /**
   * Format an ISO 8601 timestamp for display.
   *
   * @param value ISO timestamp, or null/undefined.
   * @returns A locale-formatted date/time string, or an em dash when absent.
   */
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

// PUBLIC_INTERFACE
export function toDateTimeLocalValue(value?: string | null): string {
  /**
   * Convert an ISO timestamp into a `datetime-local` input value.
   *
   * @param value ISO timestamp, or null/undefined.
   * @returns `YYYY-MM-DDTHH:mm`, or an empty string when absent/invalid.
   */
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`;
}

// PUBLIC_INTERFACE
export function fromDateTimeLocalValue(value: string): string | null {
  /**
   * Convert a `datetime-local` input value into an ISO 8601 string.
   *
   * @param value Raw input value.
   * @returns ISO string, or null when the field is empty/invalid.
   */
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}
