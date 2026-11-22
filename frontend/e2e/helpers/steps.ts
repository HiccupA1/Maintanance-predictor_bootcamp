/**
 * Records every user action a scenario performs, for the workflow benchmark
 * (tools/workflow_benchmark, Docs/stage-9/workflow-comparison.md).
 *
 * The action vocabulary matches the manual baseline
 * (tools/workflow_benchmark/baseline.json), so both flows are counted and
 * KLM-priced by the same rules:
 *   navigate: open the app or a page
 *   click:    press a button or link
 *   select:   choose from a dropdown
 *   type:     enter text into a field (chars = length)
 * System work (threshold checks, alert creation, prefilling, closure side
 * effects) is not a user action and is listed separately as `automated`.
 */
import fs from 'node:fs';
import path from 'node:path';
import type { Locator, Page } from '@playwright/test';

export type Actor = 'Operator' | 'PlantManager' | 'MaintenanceEngineer';
export type ActionType = 'navigate' | 'click' | 'select' | 'type';

export interface RecordedAction {
  actor: Actor;
  type: ActionType;
  description: string;
  chars?: number;
}

export class StepRecorder {
  readonly actions: RecordedAction[] = [];
  readonly automated: string[] = [];
  private readonly started = Date.now();

  constructor(private readonly actor: () => Actor) {}

  private log(type: ActionType, description: string, chars?: number) {
    this.actions.push({ actor: this.actor(), type, description, ...(chars !== undefined && { chars }) });
  }

  async navigate(page: Page, url: string, description: string) {
    this.log('navigate', description);
    await page.goto(url);
  }

  async click(target: Locator, description: string) {
    this.log('click', description);
    await target.click();
  }

  async select(target: Locator, value: string, description: string) {
    this.log('select', description);
    await target.selectOption(value);
  }

  async type(target: Locator, text: string, description: string) {
    this.log('type', description, text.length);
    await target.fill(text);
  }

  /** Record something the system did for the user (not a user action). */
  system(description: string) {
    this.automated.push(description);
  }

  write(file: string) {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(
      file,
      JSON.stringify(
        {
          flow: 'app',
          generated_at: new Date().toISOString(),
          automated_wall_time_s: Math.round((Date.now() - this.started) / 100) / 10,
          steps: this.actions.length,
          actions: this.actions,
          automated: this.automated,
        },
        null,
        2,
      ),
    );
  }
}
