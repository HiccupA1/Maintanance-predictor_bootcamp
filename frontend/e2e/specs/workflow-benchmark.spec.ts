/**
 * Workflow benchmark: the app flow for the scenario in
 * Docs/stage-9/workflow-baseline-sop.md, driven through the real UI by three
 * users, with every user action recorded (helpers/steps.ts).
 *
 * The scenario, identical in the manual baseline: an Operator records a
 * reading that breaches a threshold; the Plant Manager raises a work order
 * for it; the Maintenance Engineer closes it with resolution notes, root cause
 * and the failure outcome; the issue ends resolved and the asset's
 * last-service date is updated.
 *
 * Output: reports/workflow-app.json (repo root), read by
 * `python -m tools.workflow_benchmark.report`.
 */
import path from 'node:path';

import { REPO_ROOT } from '../env';
import { StepRecorder, type Actor } from '../helpers/steps';
import { signInAs, test, expect } from '../fixtures';

// The same text the manual baseline types, so typing effort is comparable.
const TEXT = {
  value: '95',
  description: 'Inspect cooling loop',
  notes: 'Replaced worn bearing',
  cause: 'Bearing wear',
};

test('workflow benchmark: breach to closed work order, recorded', async ({ browser, api }) => {
  const m = await api.machine({ name: 'Cooling pump P-101' });
  let actor: Actor = 'Operator';
  const steps = new StepRecorder(() => actor);

  // Operator records the reading.
  const op = await browser.newPage();
  await signInAs(op, 'Operator');
  await steps.navigate(op, '/', 'Open the app (lands on Readings)');
  await steps.select(op.getByLabel('Equipment'), m.equipmentId, 'Choose the machine');
  await steps.select(op.getByLabel('Parameter'), m.parameterId, 'Choose the parameter');
  await steps.type(op.getByLabel('Value'), TEXT.value, 'Enter the reading');
  await steps.click(op.getByRole('button', { name: 'Save reading' }), 'Save the reading');
  await expect(op.getByLabel('Value')).toHaveValue('');
  steps.system('Reading timestamped and attributed to the signed-in user');
  steps.system('Threshold checked (inclusive bounds)');
  steps.system('Alert raised with machine, parameter, value, limits and priority');
  const [alert] = await api.alertFor(m.equipmentPk);
  expect(alert.status).toBe('NEW');
  await op.close();

  // Plant Manager raises the work order from the alert.
  actor = 'PlantManager';
  const pm = await browser.newPage();
  await signInAs(pm, 'PlantManager');
  await steps.navigate(pm, '/', 'Open the app (lands on Alerts)');
  const alertRow = pm.getByRole('row', { name: new RegExp(m.name) });
  await steps.click(alertRow.getByRole('link').first(), 'Open the alert');
  await steps.click(pm.getByRole('link', { name: 'Convert to Work Order' }), 'Convert to a work order');
  await steps.type(pm.getByLabel('Description'), TEXT.description, 'Describe the work');
  await steps.select(pm.getByLabel('Priority'), 'HIGH', 'Set the priority');
  await steps.click(pm.getByRole('button', { name: 'Create work order' }), 'Create the work order');
  await expect(pm).toHaveURL(/\/work-orders\/[0-9a-f-]{36}$/);
  steps.system('Work order linked to the alert and prefilled with the machine');
  steps.system('Duplicate work orders for the same alert prevented');
  const workOrderId = pm.url().split('/').pop()!;
  await pm.close();

  // Maintenance Engineer closes it.
  actor = 'MaintenanceEngineer';
  const me = await browser.newPage();
  await signInAs(me, 'MaintenanceEngineer');
  await steps.navigate(me, '/', 'Open the app (lands on Work Orders)');
  // Test-only, not a user step: show every row, because other tests share the database.
  await me.getByLabel('Page size').fill('200');
  await steps.click(me.locator(`a[href="/work-orders/${workOrderId}"]`), 'Open the work order');
  await expect(me).toHaveURL(new RegExp(`/work-orders/${workOrderId}$`));
  await steps.click(me.getByRole('link', { name: 'Edit', exact: true }), 'Edit the work order');
  await steps.select(me.getByLabel('Status'), 'CLOSED', 'Set status to Closed');
  await steps.type(me.getByLabel('Resolution notes'), TEXT.notes, 'Enter resolution notes');
  await steps.type(me.getByLabel('Root cause'), TEXT.cause, 'Enter the root cause');
  await steps.select(me.getByLabel('Was this a real equipment failure?'), 'yes', 'Confirm a real failure');
  await steps.select(me.getByLabel('Failure mode'), 'TWF', 'Choose the failure mode');
  await steps.click(me.getByRole('button', { name: 'Save changes' }), 'Save the closure');
  await expect(me.getByLabel('Closure record')).toContainText('Tool wear');
  steps.system('Closure timestamped and attributed to the signed-in engineer');
  steps.system('Source alert resolved');
  steps.system("Equipment's last-service date updated");
  steps.system('Failure label stored for model retraining');
  await me.close();

  // The scenario's end state, verified.
  const [after] = await api.alertFor(m.equipmentPk);
  expect(after.status).toBe('RESOLVED');
  const eq = await api.call<{ last_service_date: string | null }>('GET', `/equipment/${m.equipmentId}`);
  expect(eq.last_service_date).not.toBeNull();

  steps.write(path.join(REPO_ROOT, 'reports', 'workflow-app.json'));
});
