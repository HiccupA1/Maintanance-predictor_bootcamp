/** Equipment registry (PRD FR1: Admins create and edit equipment). */
import { signInAs, test, expect, uid } from '../fixtures';

async function fillEquipment(
  page: import('@playwright/test').Page,
  values: Partial<Record<'Equipment ID' | 'Name' | 'Location' | 'Type' | 'Criticality', string>>,
) {
  for (const [label, value] of Object.entries(values)) {
    await page.getByLabel(label, { exact: true }).fill(value);
  }
}

test.describe('as Admin', () => {
  test.beforeEach(async ({ page }) => signInAs(page, 'Admin'));

  test('creates equipment and opens its detail page', async ({ page }) => {
    const id = `E2E-${uid()}`;
    await page.goto('/equipment/new');
    await fillEquipment(page, {
      'Equipment ID': id,
      Name: 'Cooling pump',
      Location: 'Hall 2',
      Type: 'Pump',
      Criticality: '4',
    });
    await page.getByRole('button', { name: 'Create equipment' }).click();
    await expect(page).toHaveURL(new RegExp(`/equipment/${id}$`));
    await expect(page.getByRole('heading', { level: 1, name: 'Cooling pump' })).toBeVisible();
    await expect(page.getByText('4 / 5')).toBeVisible();
  });

  test('requires every field', async ({ page }) => {
    await page.goto('/equipment/new');
    await page.getByRole('button', { name: 'Create equipment' }).click();
    await expect(page.getByText('This field is required.')).toHaveCount(4);
    await expect(page.getByText('Criticality is required.')).toBeVisible();
  });

  for (const value of ['0', '6', '2.5']) {
    test(`rejects criticality ${value}`, async ({ page }) => {
      await page.goto('/equipment/new');
      await fillEquipment(page, {
        'Equipment ID': `E2E-${uid()}`,
        Name: 'x',
        Location: 'x',
        Type: 'x',
        Criticality: value,
      });
      await page.getByRole('button', { name: 'Create equipment' }).click();
      await expect(page.getByText('Criticality must be an integer from 1 to 5.')).toBeVisible();
    });
  }

  test('reports a duplicate equipment id', async ({ page, api }) => {
    const m = await api.machine();
    await page.goto('/equipment/new');
    await fillEquipment(page, {
      'Equipment ID': m.equipmentId,
      Name: 'Duplicate',
      Location: 'x',
      Type: 'x',
      Criticality: '2',
    });
    await page.getByRole('button', { name: 'Create equipment' }).click();
    await expect(page.getByText('Could not save equipment')).toBeVisible();
    await expect(page.getByText(/already exists/)).toBeVisible();
  });

  test('edits equipment', async ({ page, api }) => {
    const m = await api.machine();
    await page.goto(`/equipment/${m.equipmentId}`);
    await page.getByRole('button', { name: 'Edit equipment' }).click();
    await page.getByLabel('Name', { exact: true }).fill('Renamed pump');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(page.getByRole('heading', { level: 1, name: 'Renamed pump' })).toBeVisible();
  });

  test('lists equipment with a link to its detail page', async ({ page, api }) => {
    const m = await api.machine();
    await page.goto('/equipment');
    const row = page.getByRole('row', { name: new RegExp(m.equipmentId) });
    await expect(row).toContainText(m.name);
    await row.getByRole('link', { name: m.equipmentId }).click();
    await expect(page).toHaveURL(new RegExp(`/equipment/${m.equipmentId}$`));
  });

  test('shows a not-found state for an unknown id', async ({ page }) => {
    await page.goto('/equipment/NO-SUCH-EQUIPMENT');
    await expect(page.getByText('Equipment not found')).toBeVisible();
  });
});

test('a Plant Manager can view equipment but not create it', async ({ page }) => {
  await signInAs(page, 'PlantManager');
  await page.goto('/equipment');
  await expect(page.getByRole('heading', { level: 1, name: 'Equipment' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Add equipment' })).toHaveCount(0);
  await page.goto('/equipment/new');
  await expect(page.getByText('Admin access required')).toBeVisible();
});
