/**
 * Role-based navigation and route guards (frontend/src/utils/rbac.ts,
 * Docs/security/authorization-matrix.md). Denied routes redirect to the
 * role's landing page.
 */
import { NAMES, ROLES, signInAs, test, expect, type Role } from '../fixtures';

const LANDING: Record<Role, string> = {
  Admin: '/work-orders',
  PlantManager: '/alerts',
  MaintenanceEngineer: '/work-orders',
  Operator: '/readings',
};

const PAGES = [
  { path: '/readings', nav: 'Readings', heading: 'Manual readings', allowed: ROLES },
  {
    path: '/work-orders',
    nav: 'Work Orders',
    heading: 'Work Orders',
    allowed: ['Admin', 'PlantManager', 'MaintenanceEngineer'],
  },
  {
    path: '/equipment',
    nav: 'Equipment',
    heading: 'Equipment',
    allowed: ['Admin', 'PlantManager', 'MaintenanceEngineer'],
  },
  {
    path: '/alerts',
    nav: 'Alerts',
    heading: 'Alerts',
    allowed: ['Admin', 'PlantManager', 'MaintenanceEngineer'],
  },
  { path: '/admin/users', nav: 'Admin', heading: 'Users & roles', allowed: ['Admin'] },
  { path: '/admin/models', nav: 'Models', heading: 'Models', allowed: ['Admin'] },
] as const;

for (const role of ROLES) {
  test(`${role} lands on ${LANDING[role]} and sees their name and role`, async ({ page }) => {
    await signInAs(page, role);
    await page.goto('/');
    await expect(page).toHaveURL(new RegExp(`${LANDING[role]}$`));
    await expect(page.getByText(NAMES[role])).toBeVisible();
    await expect(page.locator('.role-pill')).toHaveText(role);
  });

  for (const p of PAGES) {
    const allowed = (p.allowed as readonly string[]).includes(role);
    test(`${role} ${allowed ? 'can' : 'cannot'} open ${p.path}`, async ({ page }) => {
      await signInAs(page, role);
      await page.goto(p.path);
      const nav = page.getByRole('navigation', { name: 'Primary' });
      if (allowed) {
        await expect(page).toHaveURL(new RegExp(`${p.path}$`));
        await expect(page.getByRole('heading', { level: 1, name: p.heading })).toBeVisible();
        await expect(nav.getByRole('link', { name: p.nav, exact: true })).toBeVisible();
      } else {
        await expect(page).toHaveURL(new RegExp(`${LANDING[role]}$`));
        await expect(nav.getByRole('link', { name: p.nav, exact: true })).toHaveCount(0);
      }
    });
  }
}
