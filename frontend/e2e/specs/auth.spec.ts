/** Sign-in, sign-out, session persistence and safe post-login redirects. */
import { NAMES, STORAGE_KEY, signInAs, stubSupabase, test, expect, type Role } from '../fixtures';

async function signInWithForm(page: import('@playwright/test').Page, role: Role | 'fail', next = '') {
  await stubSupabase(page, role);
  await page.goto(`/login${next}`);
  await page.getByLabel('Email').fill('someone@example.com');
  await page.getByLabel('Password').fill('correct horse battery staple');
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('an anonymous visitor is sent to sign in, keeping the requested page', async ({ page }) => {
  await stubSupabase(page);
  await page.goto('/work-orders');
  await expect(page).toHaveURL(/\/login\?next=%2Fwork-orders$/);
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
});

test('signing in with the form lands an Operator on Readings', async ({ page }) => {
  await signInWithForm(page, 'Operator');
  await expect(page).toHaveURL(/\/readings$/);
  await expect(page.getByText(NAMES.Operator)).toBeVisible();
});

test('signing in returns the user to the page they asked for', async ({ page }) => {
  await signInWithForm(page, 'PlantManager', '?next=%2Fequipment');
  await expect(page).toHaveURL(/\/equipment$/);
});

test('wrong credentials show an error and stay on the sign-in page', async ({ page }) => {
  await signInWithForm(page, 'fail');
  await expect(page.getByRole('alert')).toContainText(/invalid login credentials/i);
  await expect(page).toHaveURL(/\/login/);
});

// A real backslash: browsers normalise /\host to //host (an off-site URL).
for (const next of ['/\\evil.example', '//evil.example', 'https://evil.example']) {
  test(`post-login redirect refuses an off-site target (${next})`, async ({ page }) => {
    await signInWithForm(page, 'Operator', `?next=${encodeURIComponent(next)}`);
    await expect(page).toHaveURL(/^http:\/\/127\.0\.0\.1:\d+\/readings$/);
  });
}

test('signing out clears the session and protects pages again', async ({ page }) => {
  await signInAs(page, 'MaintenanceEngineer');
  await page.goto('/work-orders');
  await page.evaluate(() => window.sessionStorage.setItem('e2e-signed-out', '1'));
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.waitForLoadState('networkidle');
  expect(await page.evaluate((k) => window.localStorage.getItem(k), STORAGE_KEY)).toBeNull();
  await page.goto('/work-orders');
  await expect(page).toHaveURL(/\/login/);
});

test('the session survives a page reload', async ({ page }) => {
  await signInAs(page, 'Admin');
  await page.goto('/equipment');
  await page.reload();
  await expect(page).toHaveURL(/\/equipment$/);
  await expect(page.getByText(NAMES.Admin)).toBeVisible();
});
