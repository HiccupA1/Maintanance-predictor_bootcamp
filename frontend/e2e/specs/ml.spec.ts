/**
 * Failure-risk scoring in the UI (WP4/WP5): shadow-first rollout, admin-only
 * shadow scores, activation raising MODEL alerts, the Models page.
 *
 * Serial, because activating the shared ai4i-v1 version changes behaviour for
 * every ai4i_milling machine. The last test returns it to shadow.
 */
import { signInAs, test, expect, uid, type Api } from '../fixtures';

const FEATURES = [
  'product_type',
  'air_temp_k',
  'process_temp_k',
  'rotational_speed_rpm',
  'torque_nm',
  'tool_wear_min',
] as const;
type Inputs = Record<(typeof FEATURES)[number], string>;

const SAFE: Inputs = {
  product_type: 'H',
  air_temp_k: '298',
  process_temp_k: '309',
  rotational_speed_rpm: '1500',
  torque_nm: '38',
  tool_wear_min: '10',
};
// Worn tool, overstrain and poor heat dissipation at low speed.
const RISKY: Inputs = {
  product_type: 'L',
  air_temp_k: '302',
  process_temp_k: '310.5',
  rotational_speed_rpm: '1300',
  torque_nm: '65',
  tool_wear_min: '230',
};

async function mappedMachine(api: Api) {
  const id = `ML-${uid()}`;
  const eq = await api.call<{ id: string; name: string }>('POST', '/equipment', {
    equipment_id: id,
    name: `Mill ${id}`,
    location: 'E2E plant',
    type: 'Mill',
    criticality: 3,
    asset_class: 'ai4i_milling',
  });
  const params: Record<string, string> = {};
  for (const key of FEATURES) {
    const p = await api.as('PlantManager').call<{ id: string }>(
      'POST',
      `/equipment/${id}/parameters`,
      { name: key, unit: '-', max_threshold: 1e9, feature_key: key },
    );
    params[key] = p.id;
  }
  return { equipmentId: id, equipmentPk: eq.id, name: eq.name, params };
}

async function recordAll(api: Api, m: Awaited<ReturnType<typeof mappedMachine>>, v: Inputs) {
  for (const key of FEATURES) await api.reading(m.equipmentId, m.params[key], v[key]);
}

async function waitForScores(api: Api, equipmentId: string, count: number) {
  await expect
    .poll(
      async () =>
        (await api.call<{ history: unknown[] }>('GET', `/equipment/${equipmentId}/risk`)).history
          .length,
      { timeout: 20_000 },
    )
    .toBeGreaterThanOrEqual(count);
}

async function modelId(api: Api) {
  const models = await api.call<{ id: string; version: string }[]>('GET', '/models');
  return models.find((m) => m.version === 'ai4i-v1')!.id;
}

test.describe.configure({ mode: 'serial' });

test.beforeAll(async ({ request }) => {
  const api = new (await import('../fixtures')).Api(request, 'Admin');
  await api.call('POST', `/models/${await modelId(api)}/stage`, { stage: 'shadow' }).catch(() => {});
});

test('equipment without a model asset class is shown as not scored', async ({ page, api }) => {
  const m = await api.machine();
  await signInAs(page, 'PlantManager');
  await page.goto(`/equipment/${m.equipmentId}`);
  await expect(page.getByLabel('Failure risk')).toContainText('Not scored');
});

test('shadow scores are hidden from a Plant Manager', async ({ page, api }) => {
  const m = await mappedMachine(api);
  await recordAll(api, m, RISKY);
  await waitForScores(api, m.equipmentId, 1);
  await signInAs(page, 'PlantManager');
  await page.goto(`/equipment/${m.equipmentId}`);
  await expect(page.getByLabel('Failure risk')).toContainText('No scores yet');
});

test('an Admin sees the shadow score, labelled as shadow', async ({ page, api }) => {
  const m = await mappedMachine(api);
  await recordAll(api, m, RISKY);
  await waitForScores(api, m.equipmentId, 1);
  await signInAs(page, 'Admin');
  await page.goto(`/equipment/${m.equipmentId}`);
  const panel = page.getByLabel('Failure risk');
  await expect(panel).toContainText(/\d+%/);
  await expect(panel).toContainText('Shadow model (ai4i-v1)');
  await expect(page.getByTestId('risk-badge')).toHaveText('At risk');
});

test('the Models page shows the shadow evaluation and drift', async ({ page }) => {
  await signInAs(page, 'Admin');
  await page.goto('/admin/models');
  const card = page.getByRole('article').filter({ hasText: 'ai4i-v1' });
  await expect(card).toContainText('shadow');
  await expect(card.getByText(/Shadow evaluation/)).toBeVisible();
  await expect(card.getByText('This model')).toBeVisible();
  await expect(card.getByText('Threshold alerts')).toBeVisible();
  await expect(card.getByText(/Drift/)).toBeVisible();
});

test('an Admin activates the model from the Models page', async ({ page }) => {
  await signInAs(page, 'Admin');
  page.on('dialog', (dialog) => void dialog.accept());
  await page.goto('/admin/models');
  const card = page.getByRole('article').filter({ hasText: 'ai4i-v1' });
  await card.getByRole('button', { name: 'Activate' }).click();
  await expect(card.getByRole('button', { name: 'Move to shadow' })).toBeVisible();
  await expect(card).toContainText(/stage set by Ada Admin/);
});

test('an active model raises a MODEL alert that users can see', async ({ page, api }) => {
  const m = await mappedMachine(api);
  await recordAll(api, m, RISKY);
  await expect
    .poll(async () => (await api.alertFor(m.equipmentPk)).filter((a) => a.source === 'MODEL').length, {
      timeout: 20_000,
    })
    .toBe(1);
  await signInAs(page, 'PlantManager');
  await page.goto('/alerts');
  const row = page.getByRole('row', { name: new RegExp(m.name) });
  await expect(row.getByText('Model', { exact: true })).toBeVisible();
  await row.getByRole('link').first().click();
  await expect(page.getByText('Raised by risk model')).toBeVisible();
  await page.goto(`/equipment/${m.equipmentId}`);
  await expect(page.getByTestId('risk-badge')).toHaveText('At risk');
});

test('a normal reading on an active model resolves its MODEL alert', async ({ api }) => {
  const m = await mappedMachine(api);
  await recordAll(api, m, RISKY);
  await expect
    .poll(async () => (await api.alertFor(m.equipmentPk)).filter((a) => a.source === 'MODEL').length, {
      timeout: 20_000,
    })
    .toBe(1);
  await recordAll(api, m, SAFE);
  await expect
    .poll(
      async () =>
        (await api.alertFor(m.equipmentPk)).find((a) => a.source === 'MODEL')?.status,
      { timeout: 20_000 },
    )
    .toBe('RESOLVED');
});

test('an Admin returns the model to shadow', async ({ page }) => {
  await signInAs(page, 'Admin');
  page.on('dialog', (dialog) => void dialog.accept());
  await page.goto('/admin/models');
  const card = page.getByRole('article').filter({ hasText: 'ai4i-v1' });
  await card.getByRole('button', { name: 'Move to shadow' }).click();
  await expect(card.getByRole('button', { name: 'Activate' })).toBeVisible();
});
