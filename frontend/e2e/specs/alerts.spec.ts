/** Alert triage and conversion to one linked work order (PRD FR7). */
import { signInAs, test, expect } from '../fixtures';

test.describe('as Plant Manager', () => {
  test.beforeEach(async ({ page }) => signInAs(page, 'PlantManager'));

  test('lists a breach with its equipment and parameter', async ({ page, api }) => {
    const m = await api.machineWithAlert();
    await page.goto('/alerts');
    const row = page.getByRole('row', { name: new RegExp(m.name) });
    await expect(row).toContainText('Temperature');
    await expect(row).toContainText('95');
    await expect(row).toContainText('NEW');
  });

  test('opens alert detail with the conversion action', async ({ page, api }) => {
    const m = await api.machineWithAlert();
    await page.goto(`/alerts/${m.alertId}`);
    await expect(page.getByRole('heading', { level: 1, name: 'Alert detail' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Convert to Work Order' })).toBeVisible();
  });

  test('converts an alert into one work order linked to it', async ({ page, api }) => {
    const m = await api.machineWithAlert();
    await page.goto(`/alerts/${m.alertId}`);
    await page.getByRole('link', { name: 'Convert to Work Order' }).click();
    await page.getByLabel('Description').fill('Inspect the cooling loop');
    await page.getByLabel('Priority').selectOption('CRITICAL');
    await page.getByRole('button', { name: 'Create work order' }).click();
    await expect(page).toHaveURL(/\/work-orders\/[0-9a-f-]{36}$/);
    const id = page.url().split('/').pop()!;
    const wo = await api.as('PlantManager').call<{ alert_id: string; equipment_id: string; priority: string }>(
      'GET',
      `/work-orders/${id}`,
    );
    expect(wo.alert_id).toBe(m.alertId);
    expect(wo.equipment_id).toBe(m.equipmentPk);
    expect(wo.priority).toBe('CRITICAL');
  });

  test('refuses a second work order for the same alert', async ({ page, api }) => {
    const m = await api.machineWithAlert();
    await api.as('PlantManager').call('POST', '/work-orders', {
      title: 'First',
      priority: 'HIGH',
      alert_id: m.alertId,
    });
    await page.goto(`/alerts/${m.alertId}/convert`);
    await page.getByLabel('Description').fill('Again');
    await page.getByRole('button', { name: 'Create work order' }).click();
    await expect(page.getByText('Work order creation conflicted with current state.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create work order' })).toBeDisabled();
  });

  test('shows a not-found state for an unknown alert', async ({ page }) => {
    await page.goto('/alerts/00000000-0000-0000-0000-000000000000');
    await expect(page.getByText('Alert not found')).toBeVisible();
  });
});

test('a Maintenance Engineer sees alerts but cannot convert them', async ({ page, api }) => {
  const m = await api.machineWithAlert();
  await signInAs(page, 'MaintenanceEngineer');
  await page.goto(`/alerts/${m.alertId}`);
  await expect(page.getByRole('heading', { level: 1, name: 'Alert detail' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Convert to Work Order' })).toHaveCount(0);
});
