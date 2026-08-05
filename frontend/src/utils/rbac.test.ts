import { describe, expect, it } from 'vitest';

import { canAccessPage, hasRole } from './rbac';

describe('hasRole', () => {
  it('returns true when the role is allowed', () => {
    expect(hasRole('Admin', ['Admin', 'PlantManager'])).toBe(true);
  });

  it('returns false when the role is not allowed or absent', () => {
    expect(hasRole('Operator', ['Admin', 'PlantManager'])).toBe(false);
    expect(hasRole(undefined, ['Admin'])).toBe(false);
  });
});

describe('canAccessPage', () => {
  it('matches the clarified PRD navigation matrix', () => {
    expect(canAccessPage('Admin', 'equipment')).toBe(true);
    expect(canAccessPage('Admin', 'admin')).toBe(true);
    expect(canAccessPage('Admin', 'readings')).toBe(false);

    expect(canAccessPage('PlantManager', 'work-orders')).toBe(true);
    expect(canAccessPage('PlantManager', 'equipment')).toBe(true);
    expect(canAccessPage('PlantManager', 'admin')).toBe(false);

    expect(canAccessPage('MaintenanceEngineer', 'alerts')).toBe(true);
    expect(canAccessPage('MaintenanceEngineer', 'equipment')).toBe(true);
    expect(canAccessPage('MaintenanceEngineer', 'admin')).toBe(false);

    expect(canAccessPage('Operator', 'readings')).toBe(true);
    expect(canAccessPage('Operator', 'equipment')).toBe(false);
    expect(canAccessPage('Operator', 'work-orders')).toBe(false);
  });

  it('does not expose pages for an absent or unknown role', () => {
    expect(canAccessPage(undefined, 'admin')).toBe(false);
    expect(canAccessPage('UnknownRole', 'equipment')).toBe(false);
  });
});
