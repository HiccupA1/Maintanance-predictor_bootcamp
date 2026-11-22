/**
 * Manual readings and threshold alerts (PRD FR3 to FR6): inclusive bounds,
 * one active alert per breach stream, recovery clears the alert.
 */
import { NAMES, signInAs, test, expect, type Api } from '../fixtures';
import type { Page } from '@playwright/test';

type Machine = Awaited<ReturnType<Api['machine']>>;

async function record(page: Page, m: Machine, value: string) {
  await page.getByLabel('Equipment').selectOption(m.equipmentId);
  await page.getByLabel('Parameter').selectOption(m.parameterId);
  await page.getByLabel('Value').fill(value);
  await page.getByRole('button', { name: 'Save reading' }).click();
  await expect(page.getByLabel('Value')).toHaveValue('');
}

async function activeAlerts(api: Api, m: Machine) {
  return (await api.alertFor(m.equipmentPk)).filter((a) => ['NEW', 'IN_PROGRESS'].includes(a.status));
}

test.describe('as Operator', () => {
  test.beforeEach(async ({ page }) => {
    await signInAs(page, 'Operator');
    await page.goto('/readings');
  });

  test('records an in-range reading under the verified name, with no alert', async ({ page, api }) => {
    const m = await api.machine();
    await record(page, m, '42');
    const row = page.getByTestId('reading-history').getByRole('row', { name: /42/ });
    await expect(row).toContainText(NAMES.Operator);
    await expect(row).toContainText('Original');
    expect(await activeAlerts(api, m)).toHaveLength(0);
  });

  test('a reading exactly at the maximum raises an alert (inclusive)', async ({ page, api }) => {
    const m = await api.machine({ min: 10, max: 80 });
    await record(page, m, '80');
    await expect.poll(async () => (await activeAlerts(api, m)).length).toBe(1);
  });

  test('a reading exactly at the minimum raises an alert (inclusive)', async ({ page, api }) => {
    const m = await api.machine({ min: 10, max: 80 });
    await record(page, m, '10');
    await expect.poll(async () => (await activeAlerts(api, m)).length).toBe(1);
  });

  test('a breach on critical equipment is raised as CRITICAL', async ({ page, api }) => {
    const m = await api.machine({ criticality: 5 });
    await record(page, m, '95');
    const [alert] = await activeAlerts(api, m);
    expect((alert as unknown as { priority: string }).priority).toBe('CRITICAL');
  });

  test('a breach on ordinary equipment is raised as HIGH', async ({ page, api }) => {
    const m = await api.machine({ criticality: 2 });
    await record(page, m, '95');
    const [alert] = await activeAlerts(api, m);
    expect((alert as unknown as { priority: string }).priority).toBe('HIGH');
  });

  test('a repeat breach updates the open alert instead of adding one', async ({ page, api }) => {
    const m = await api.machine();
    await record(page, m, '90');
    await record(page, m, '97');
    const alerts = await activeAlerts(api, m);
    expect(alerts).toHaveLength(1);
    expect((alerts[0] as unknown as { current_value: string }).current_value).toBe('97');
  });

  test('an in-range reading after a breach resolves the alert', async ({ page, api }) => {
    const m = await api.machine();
    await record(page, m, '99');
    await record(page, m, '50');
    expect(await activeAlerts(api, m)).toHaveLength(0);
    const all = await api.alertFor(m.equipmentPk);
    expect(all.map((a) => a.status)).toEqual(['RESOLVED']);
  });

  test('a non-numeric observation is stored and raises no alert', async ({ page, api }) => {
    const m = await api.machine();
    await record(page, m, 'abnormal vibration');
    await expect(
      page.getByTestId('reading-history').getByRole('row', { name: /abnormal vibration/ }),
    ).toBeVisible();
    expect(await activeAlerts(api, m)).toHaveLength(0);
  });

  test('validates the capture form', async ({ page }) => {
    await page.getByRole('button', { name: 'Save reading' }).click();
    await expect(page.getByText('Equipment is required.')).toBeVisible();
    await expect(page.getByText('Parameter is required.')).toBeVisible();
    await expect(page.getByText('Value is required.')).toBeVisible();
  });

  test('corrects a recent reading with a reason', async ({ page, api }) => {
    const m = await api.machine();
    await record(page, m, '33');
    const row = page.getByTestId('reading-history').getByRole('row', { name: /33/ });
    await row.getByRole('button', { name: 'Edit' }).click();
    const correction = page.getByPlaceholder('Explain why this reading is being corrected');
    const form = page.locator('form').filter({ has: correction });
    await form.getByRole('textbox').first().fill('34');
    await correction.fill('Transcription error');
    await form.getByRole('button').first().click();
    await expect(
      page.getByTestId('reading-history').getByRole('row', { name: /34/ }),
    ).toContainText(`Modified by ${NAMES.Operator}`);
  });
});

test('a Plant Manager can review readings but the capture form is disabled', async ({ page }) => {
  await signInAs(page, 'PlantManager');
  await page.goto('/readings');
  await expect(page.getByText('Operator access required')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save reading' })).toBeDisabled();
  await expect(page.getByLabel('Value')).toBeDisabled();
});
