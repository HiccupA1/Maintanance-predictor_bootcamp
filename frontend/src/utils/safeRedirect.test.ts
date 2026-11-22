import { describe, expect, it } from 'vitest';

import { safeNextPath } from './safeRedirect';

describe('safeNextPath', () => {
  it.each([
    ['/work-orders', '/work-orders'],
    ['/alerts/123?tab=details#notes', '/alerts/123?tab=details#notes'],
    ['/', '/'],
  ])('allows in-app path %s', (raw, expected) => {
    expect(safeNextPath(raw)).toBe(expected);
  });

  it.each([
    null,
    undefined,
    '',
    'work-orders',
    'https://evil.example',
    '//evil.example',
    '/\\evil.example',
    '/\\/evil.example',
    '\\\\evil.example',
    '/\tevil.example',
    '/\n/evil.example',
    'javascript:alert(1)',
    `/${'a'.repeat(3000)}`,
  ])('rejects unsafe target %j', (raw) => {
    expect(safeNextPath(raw)).toBeNull();
  });
});
