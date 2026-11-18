import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import * as riskApi from '../../api/risk';
import { RiskPanel } from './RiskPanel';

const score = (over: Partial<riskApi.RiskScore> = {}): riskApi.RiskScore => ({
  id: 's1',
  model_version_id: 'm1',
  model_version: 'ai4i-v1',
  score: 0.82,
  flagged: true,
  stage: 'active',
  features: {},
  scored_at: '2026-11-19T10:00:00Z',
  ...over,
});

describe('RiskPanel', () => {
  afterEach(() => vi.restoreAllMocks());

  it('shows the latest score and an at-risk badge', async () => {
    vi.spyOn(riskApi, 'getEquipmentRisk').mockResolvedValue({
      equipment_id: 'eq-1',
      asset_class: 'ai4i_milling',
      status: 'scored',
      latest: score(),
      history: [score()],
    });
    render(<RiskPanel equipmentId="eq-1" />);
    expect(await screen.findByText('82%')).toBeInTheDocument();
    expect(screen.getByTestId('risk-badge')).toHaveTextContent('At risk');
  });

  it('labels shadow scores as admin-only', async () => {
    vi.spyOn(riskApi, 'getEquipmentRisk').mockResolvedValue({
      equipment_id: 'eq-1',
      asset_class: 'ai4i_milling',
      status: 'scored',
      latest: score({ stage: 'shadow', flagged: false, score: 0.1 }),
      history: [score({ stage: 'shadow', flagged: false, score: 0.1 })],
    });
    render(<RiskPanel equipmentId="eq-1" />);
    expect(await screen.findByText(/Shadow model/)).toBeInTheDocument();
    expect(screen.getByTestId('risk-badge')).toHaveTextContent('Normal');
  });

  it('explains when equipment is not configured for scoring', async () => {
    vi.spyOn(riskApi, 'getEquipmentRisk').mockResolvedValue({
      equipment_id: 'eq-1',
      asset_class: null,
      status: 'not_configured',
      latest: null,
      history: [],
    });
    render(<RiskPanel equipmentId="eq-1" />);
    expect(await screen.findByText(/Not scored/)).toBeInTheDocument();
  });
});
