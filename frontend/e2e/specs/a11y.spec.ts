/**
 * Automated accessibility checks (axe-core, WCAG 2.1 A/AA rules) on each main
 * page. Fails on serious or critical violations. Automated checks catch only
 * part of WCAG; they do not replace a manual audit.
 */
import AxeBuilder from '@axe-core/playwright';
import { signInAs, stubSupabase, test, expect, type Role } from '../fixtures';

const PAGES: { name: string; path: string; role: Role | null; ready: string }[] = [
  { name: 'sign-in', path: '/login', role: null, ready: 'Welcome back' },
  { name: 'readings', path: '/readings', role: 'Operator', ready: 'Manual readings' },
  { name: 'work orders', path: '/work-orders', role: 'PlantManager', ready: 'Work Orders' },
  { name: 'equipment', path: '/equipment', role: 'Admin', ready: 'Equipment' },
  { name: 'alerts', path: '/alerts', role: 'PlantManager', ready: 'Alerts' },
  { name: 'admin users', path: '/admin/users', role: 'Admin', ready: 'Users & roles' },
  { name: 'models', path: '/admin/models', role: 'Admin', ready: 'Models' },
];

for (const p of PAGES) {
  test(`${p.name} page has no serious or critical accessibility violations`, async ({ page }) => {
    if (p.role) await signInAs(page, p.role);
    else await stubSupabase(page);
    await page.goto(p.path);
    await expect(page.getByRole('heading', { level: 1, name: p.ready })).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    const blocking = results.violations.filter((v) =>
      ['serious', 'critical'].includes(v.impact ?? ''),
    );
    expect(
      blocking.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s) - ${v.help}`),
    ).toEqual([]);
  });
}

test('equipment detail page has no serious or critical accessibility violations', async ({
  page,
  api,
}) => {
  const m = await api.machine();
  await signInAs(page, 'PlantManager');
  await page.goto(`/equipment/${m.equipmentId}`);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  const blocking = results.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(blocking.map((v) => `${v.id} (${v.impact}): ${v.help}`)).toEqual([]);
});
