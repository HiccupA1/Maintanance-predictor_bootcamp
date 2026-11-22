/**
 * Work orders: list, edit (FR8), closure with failure labels (FR9), and
 * closure side effects (FR10: alert resolved, service date updated).
 */
import { NAMES, signInAs, test, expect, uid, type Api } from '../fixtures';
import type { Page } from '@playwright/test';

async function workOrderFromAlert(api: Api, title = `WO ${uid()}`) {
  const m = await api.machineWithAlert();
  const wo = await api.as('PlantManager').call<{ id: string }>('POST', '/work-orders', {
    title,
    priority: 'HIGH',
    alert_id: m.alertId,
  });
  return { ...m, workOrderId: wo.id, title };
}

async function openClosure(page: Page, id: string) {
  await page.goto(`/work-orders/${id}/edit`);
  await page.getByLabel('Status').selectOption('CLOSED');
}

async function fillClosure(
  page: Page,
  v: { notes?: string; cause?: string; confirmed?: 'yes' | 'no'; mode?: string },
) {
  if (v.notes) await page.getByLabel('Resolution notes').fill(v.notes);
  if (v.cause) await page.getByLabel('Root cause').fill(v.cause);
  if (v.confirmed) await page.getByLabel('Was this a real equipment failure?').selectOption(v.confirmed);
  if (v.mode) await page.getByLabel('Failure mode').selectOption(v.mode);
  await page.getByRole('button', { name: 'Save changes' }).click();
}

test.describe('as Maintenance Engineer', () => {
  test.beforeEach(async ({ page }) => signInAs(page, 'MaintenanceEngineer'));

  test('the detail page is titled by the work order', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await page.goto(`/work-orders/${w.workOrderId}`);
    await expect(page.getByRole('heading', { level: 1, name: w.title })).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).not.toContainText('undefined');
  });

  test('closing reveals the closure record fields', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await expect(page.getByRole('group', { name: 'Closure record' })).toBeVisible();
  });

  test('closure requires resolution notes', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await fillClosure(page, { cause: 'Bearing', confirmed: 'yes', mode: 'TWF' });
    await expect(page.getByText('Resolution notes are required to close.')).toBeVisible();
  });

  test('closure requires a root cause', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await fillClosure(page, { notes: 'Replaced', confirmed: 'yes', mode: 'TWF' });
    await expect(page.getByText('Root cause is required to close.')).toBeVisible();
  });

  test('closure requires saying whether it was a failure', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await fillClosure(page, { notes: 'Replaced', cause: 'Bearing' });
    await expect(page.getByText('Say whether a failure was confirmed.')).toBeVisible();
  });

  test('a confirmed failure requires a failure mode', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await fillClosure(page, { notes: 'Replaced', cause: 'Bearing', confirmed: 'yes' });
    await expect(page.getByText('Select the failure mode.')).toBeVisible();
  });

  test('closing records the label, resolves the alert and updates the service date', async ({
    page,
    api,
  }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await fillClosure(page, {
      notes: 'Replaced worn bearing',
      cause: 'Bearing wear',
      confirmed: 'yes',
      mode: 'TWF',
    });
    await expect(page).toHaveURL(new RegExp(`/work-orders/${w.workOrderId}$`));
    const record = page.getByLabel('Closure record');
    await expect(record).toContainText('Tool wear');
    await expect(record).toContainText('Bearing wear');

    const wo = await api.as('PlantManager').call<Record<string, unknown>>('GET', `/work-orders/${w.workOrderId}`);
    expect(wo).toMatchObject({
      status: 'CLOSED',
      failure_confirmed: true,
      failure_mode: 'TWF',
      closed_by: NAMES.MaintenanceEngineer,
    });
    const [alert] = await api.alertFor(w.equipmentPk);
    expect(alert.status).toBe('RESOLVED');
    const eq = await api.call<{ last_service_date: string | null }>('GET', `/equipment/${w.equipmentId}`);
    expect(eq.last_service_date).not.toBeNull();
  });

  test('a false alarm is closed without a failure mode', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await openClosure(page, w.workOrderId);
    await page.getByLabel('Was this a real equipment failure?').selectOption('no');
    await expect(page.getByLabel('Failure mode')).toHaveCount(0);
    await fillClosure(page, { notes: 'Sensor glitch', cause: 'Loose connector' });
    await expect(page.getByLabel('Closure record')).toContainText('No');
  });

  test('a closed work order cannot be edited', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await api.as('MaintenanceEngineer').call('PUT', `/work-orders/${w.workOrderId}`, {
      status: 'CLOSED',
      resolution_notes: 'Done',
      root_cause: 'Wear',
      failure_confirmed: false,
    });
    await page.goto(`/work-orders/${w.workOrderId}`);
    await expect(page.getByRole('link', { name: 'Edit', exact: true })).toHaveCount(0);
    await page.goto(`/work-orders/${w.workOrderId}/edit`);
    await expect(page.getByText('Closed work orders cannot be modified.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Save changes' })).toBeDisabled();
  });
});

test.describe('as Plant Manager', () => {
  test.beforeEach(async ({ page }) => signInAs(page, 'PlantManager'));

  test('edits an open work order', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await page.goto(`/work-orders/${w.workOrderId}`);
    await page.getByRole('link', { name: 'Edit', exact: true }).click();
    await page.getByLabel('Title').fill('Rebuild pump seal');
    await page.getByLabel('Assigned to').fill('Mia Engineer');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(page.getByRole('heading', { level: 1, name: 'Rebuild pump seal' })).toBeVisible();
    await expect(page.getByText('Mia Engineer').first()).toBeVisible();
  });

  test('filters the list by status', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await page.goto('/work-orders');
    await page.getByLabel('Page size').fill('200');
    await page.getByLabel('Status').selectOption('OPEN');
    await expect(page.getByRole('link', { name: w.title })).toBeVisible();
    await page.getByLabel('Status').selectOption('CLOSED');
    await expect(page.getByRole('link', { name: w.title })).toHaveCount(0);
  });

  test('filters the list by priority', async ({ page, api }) => {
    const w = await workOrderFromAlert(api);
    await page.goto('/work-orders');
    await page.getByLabel('Page size').fill('200');
    await page.getByLabel('Priority').selectOption('HIGH');
    await expect(page.getByRole('link', { name: w.title })).toBeVisible();
    await page.getByLabel('Priority').selectOption('MEDIUM');
    await expect(page.getByRole('link', { name: w.title })).toHaveCount(0);
  });

  test('loads the maximum page size (D4 regression)', async ({ page, api }) => {
    await workOrderFromAlert(api);
    await page.goto('/work-orders');
    await page.getByLabel('Page size').fill('200');
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByText('Unable to load work orders')).toHaveCount(0);
  });

  test('shows a not-found state for an unknown work order', async ({ page }) => {
    await page.goto('/work-orders/00000000-0000-0000-0000-000000000000');
    await expect(page.getByText('Work order not found')).toBeVisible();
  });
});
