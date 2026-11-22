/** Parameters and thresholds (PRD FR2: Plant Managers configure them). */
import { signInAs, test, expect } from '../fixtures';

test.describe('as Plant Manager', () => {
  test.beforeEach(async ({ page }) => signInAs(page, 'PlantManager'));

  async function openAddForm(page: import('@playwright/test').Page, equipmentId: string) {
    await page.goto(`/equipment/${equipmentId}`);
    await page.getByRole('button', { name: 'Add parameter' }).click();
  }

  test('adds a parameter with thresholds', async ({ page, api }) => {
    const m = await api.machine();
    await openAddForm(page, m.equipmentId);
    await page.getByLabel('Name').fill('Vibration');
    await page.getByLabel('Unit').fill('mm/s');
    await page.getByLabel('Minimum threshold').fill('1');
    await page.getByLabel('Maximum threshold').fill('7.5');
    await page.getByRole('button', { name: 'Save parameter' }).click();
    const row = page.getByTestId('equipment-parameters').getByRole('row', { name: /Vibration/ });
    await expect(row).toContainText('mm/s');
    await expect(row).toContainText('7.5');
  });

  test('requires at least one threshold', async ({ page, api }) => {
    const m = await api.machine();
    await openAddForm(page, m.equipmentId);
    await page.getByLabel('Name').fill('Noise');
    await page.getByLabel('Unit').fill('dB');
    await page.getByRole('button', { name: 'Save parameter' }).click();
    await expect(
      page.getByText('At least one minimum or maximum threshold is required.'),
    ).toBeVisible();
  });

  test('rejects a minimum above the maximum', async ({ page, api }) => {
    const m = await api.machine();
    await openAddForm(page, m.equipmentId);
    await page.getByLabel('Name').fill('Pressure');
    await page.getByLabel('Unit').fill('bar');
    await page.getByLabel('Minimum threshold').fill('9');
    await page.getByLabel('Maximum threshold').fill('3');
    await page.getByRole('button', { name: 'Save parameter' }).click();
    await expect(
      page.getByText('Minimum threshold must not exceed maximum threshold.'),
    ).toBeVisible();
  });

  test('requires a name and unit', async ({ page, api }) => {
    const m = await api.machine();
    await openAddForm(page, m.equipmentId);
    await page.getByLabel('Maximum threshold').fill('3');
    await page.getByRole('button', { name: 'Save parameter' }).click();
    await expect(page.getByText('Name is required.')).toBeVisible();
    await expect(page.getByText('Unit is required.')).toBeVisible();
  });

  test('edits an existing threshold', async ({ page, api }) => {
    const m = await api.machine();
    await page.goto(`/equipment/${m.equipmentId}`);
    const row = page.getByTestId('equipment-parameters').getByRole('row', { name: /Temperature/ });
    await row.getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Maximum threshold').fill('65');
    await page.getByRole('button', { name: 'Save parameter' }).click();
    await expect(row).toContainText('65');
  });

  test('cannot edit the equipment record itself', async ({ page, api }) => {
    const m = await api.machine();
    await page.goto(`/equipment/${m.equipmentId}`);
    await expect(page.getByRole('heading', { name: 'Parameters and thresholds' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Edit equipment' })).toHaveCount(0);
  });
});

test('an Admin sees parameters but cannot add them', async ({ page, api }) => {
  await signInAs(page, 'Admin');
  const m = await api.machine();
  await page.goto(`/equipment/${m.equipmentId}`);
  await expect(page.getByTestId('equipment-parameters')).toContainText('Temperature');
  await expect(page.getByRole('button', { name: 'Add parameter' })).toHaveCount(0);
});
