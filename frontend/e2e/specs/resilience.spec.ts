/** Error states the user can recover from; unknown routes. */
import { API_URL } from '../env';
import { signInAs, test, expect } from '../fixtures';

test('a failed list load shows an error with a working retry', async ({ page }) => {
  await signInAs(page, 'PlantManager');
  let block = true;
  await page.route(`${API_URL}/v1/work-orders*`, (route) =>
    block ? route.abort('connectionrefused') : route.continue(),
  );
  await page.goto('/work-orders');
  await expect(page.getByText('Unable to load work orders')).toBeVisible();
  block = false;
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByText('Unable to load work orders')).toHaveCount(0);
  await expect(page.getByRole('heading', { level: 1, name: 'Work Orders' })).toBeVisible();
});

test('if the profile cannot be loaded the user sees why, not a redirect loop', async ({ page }) => {
  await signInAs(page, 'Operator');
  await page.route(`${API_URL}/v1/me`, (route) =>
    route.fulfill({ status: 503, json: { status: 503, code: 'dependency_unavailable', title: 'Unavailable' } }),
  );
  await page.goto('/readings');
  await expect(page.getByText('Unable to confirm your access')).toBeVisible();
  await expect(page).toHaveURL(/\/readings$/);
});

test('the header reports when the API is unreachable', async ({ page }) => {
  await signInAs(page, 'Admin');
  await page.route(`${API_URL}/v1/health*`, (route) => route.abort('connectionrefused'));
  await page.goto('/equipment');
  await expect(page.getByText('API unreachable')).toBeVisible();
});

test('the header reports a healthy API', async ({ page }) => {
  await signInAs(page, 'Admin');
  await page.goto('/equipment');
  await expect(page.getByText('API online')).toBeVisible();
});

test('an unknown route shows a not-found page', async ({ page }) => {
  await signInAs(page, 'Admin');
  await page.goto('/no-such-page');
  await expect(page.getByText('Page not found')).toBeVisible();
});
