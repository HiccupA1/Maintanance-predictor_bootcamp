/**
 * Failure-risk API (WP4).
 *
 * Endpoint: GET /v1/equipment/{equipment_id}/risk
 * Shadow-stage scores are returned to Admins only (ADR-0006).
 */

import { apiRequest } from './client';

// PUBLIC_INTERFACE
export interface RiskScore {
  id: string;
  model_version_id: string;
  model_version?: string | null;
  /** Probability of failure in [0, 1]. */
  score: number;
  /** True when the score is at or above the model's alert threshold. */
  flagged: boolean;
  stage: 'shadow' | 'active' | (string & {});
  features: Record<string, number>;
  scored_at: string;
}

// PUBLIC_INTERFACE
export interface EquipmentRisk {
  equipment_id: string;
  asset_class: string | null;
  /** scored | not_configured | no_scores */
  status: 'scored' | 'not_configured' | 'no_scores' | (string & {});
  latest: RiskScore | null;
  history: RiskScore[];
}

// PUBLIC_INTERFACE
export function getEquipmentRisk(
  equipmentId: string,
  signal?: AbortSignal,
): Promise<EquipmentRisk> {
  /** Fetch the latest risk score and recent history for one equipment. */
  return apiRequest<EquipmentRisk>(
    `/equipment/${encodeURIComponent(equipmentId)}/risk`,
    { signal, query: { limit: 20 } },
  );
}
