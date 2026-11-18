import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import * as modelsApi from '../../api/models';
import { ModelsPage } from './ModelsPage';

const stats = (over: Partial<modelsApi.WarningStats> = {}): modelsApi.WarningStats => ({
  warnings: 4,
  true_positive: 3,
  false_positive: 1,
  pending: 0,
  precision: 0.75,
  failures: 4,
  failures_detected: 3,
  recall: 0.75,
  median_lead_hours: 36,
  ...over,
});

describe('ModelsPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('shows shadow evaluation against threshold alerts and drift status', async () => {
    vi.spyOn(modelsApi, 'listModels').mockResolvedValue([
      {
        id: 'm1',
        version: 'ai4i-v1',
        kind: 'failure_risk',
        asset_class: 'ai4i_milling',
        stage: 'shadow',
        threshold: 0.04,
        features: [],
        created_at: '2026-11-19T10:00:00Z',
      },
    ]);
    vi.spyOn(modelsApi, 'getModelEvaluation').mockResolvedValue({
      model_version: 'ai4i-v1',
      window_days: 90,
      horizon_days: 7,
      scores: 120,
      equipment: 6,
      model: stats(),
      threshold_alerts: stats({ precision: 0.5, recall: 0.25, failures_detected: 1 }),
      notes: [],
    });
    vi.spyOn(modelsApi, 'getModelDrift').mockResolvedValue({
      model_version: 'ai4i-v1',
      window_days: 7,
      status: 'moderate',
      samples: 120,
      score: { psi: 0.05, level: 'stable' },
      features: { air_temp_k: { psi: 0.18, level: 'moderate' } },
    });

    render(<ModelsPage />);
    expect(await screen.findByText(/120 scores on 6 machines/)).toBeInTheDocument();
    expect(screen.getByText('This model')).toBeInTheDocument();
    expect(screen.getByText('Threshold alerts')).toBeInTheDocument();
    expect(screen.getByText(/air_temp_k: PSI 0.18/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Activate' })).toBeInTheDocument();
  });
});
