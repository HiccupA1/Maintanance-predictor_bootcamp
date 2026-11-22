/** Admin user and role management (roles live only in user_profiles). */
import { randomUUID } from 'node:crypto';
import { signInAs, test, expect, uid } from '../fixtures';

test.beforeEach(async ({ page }) => {
  await signInAs(page, 'Admin');
  page.on('dialog', (dialog) => void dialog.accept());
});

test('lists application users with their roles', async ({ page }) => {
  await page.goto('/admin/users');
  const row = page.getByRole('row', { name: /operator@testenv\.invalid/ });
  await expect(row).toContainText('Operator');
});

test('adds a user with a role', async ({ page }) => {
  const email = `new-${uid().toLowerCase()}@example.com`;
  await page.goto('/admin/users');
  await page.getByLabel('Supabase user ID').fill(randomUUID());
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Display name').fill('New Starter');
  await page.getByLabel('Role').selectOption('MaintenanceEngineer');
  await page.getByRole('button', { name: 'Add user' }).click();
  await expect(page.getByRole('row', { name: new RegExp(email) })).toContainText(
    'MaintenanceEngineer',
  );
});

test("changes a user's role", async ({ page, api }) => {
  const email = `promote-${uid().toLowerCase()}@example.com`;
  await api.call('POST', '/admin/users', {
    supabase_user_id: randomUUID(),
    email,
    display_name: 'Promotable',
    role: 'Operator',
  });
  await page.goto('/admin/users');
  const row = page.getByRole('row', { name: new RegExp(email) });
  await row.getByRole('button', { name: 'Edit' }).click();
  await page.getByLabel('Role').selectOption('PlantManager');
  await page.getByRole('button', { name: 'Save changes' }).click();
  await expect(row).toContainText('PlantManager');
});

test('deletes a user after confirmation', async ({ page, api }) => {
  const email = `leaver-${uid().toLowerCase()}@example.com`;
  await api.call('POST', '/admin/users', {
    supabase_user_id: randomUUID(),
    email,
    display_name: 'Leaver',
    role: 'Operator',
  });
  await page.goto('/admin/users');
  const row = page.getByRole('row', { name: new RegExp(email) });
  await row.getByRole('button', { name: 'Delete' }).click();
  await expect(row).toHaveCount(0);
});
