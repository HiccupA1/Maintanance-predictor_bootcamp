import { describe, expect, it } from 'vitest';

import { hasRole } from './rbac';

describe('hasRole', () => {
  it('returns true when the role is allowed', () => {
    expect(hasRole('Admin', ['Admin', 'PlantManager'])).toBe(true);
  });

  it('returns false when the role is not allowed or absent', () => {
    expect(hasRole('Operator', ['Admin', 'PlantManager'])).toBe(false);
    expect(hasRole(undefined, ['Admin'])).toBe(false);
  });
});
