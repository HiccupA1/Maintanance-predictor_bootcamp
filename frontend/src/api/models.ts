/**
 * Model registry API (Admin only; WP4/WP5).
 *
 * - GET  /v1/models
 * - POST /v1/models/{id}/stage
 * - GET  /v1/models/{id}/evaluation
 * - GET  /v1/models/{id}/drift
 */

import { apiRequest } from './client';

// PUBLIC_INTERFACE
export type ModelStage = 'shadow' | 'active' | 'retired';

// PUBLIC_INTERFACE
export interface ModelVersion {
  id: string;
  version: string;
  kind: string;
  asset_class: string;
  stage: ModelStage;
  threshold: number;
  features: string[];
  metrics?: Record<string, unknown> | null;
  created_at: string;
  stage_changed_at?: string | null;
  stage_changed_by?: string | null;
}

// PUBLIC_INTERFACE
export interface WarningStats {
  warnings: number;
  true_positive: number;
  false_positive: number;
  pending: number;
  precision: number | null;
  failures: number;
  failures_detected: number;
  recall: number | null;
  median_lead_hours: number | null;
}

// PUBLIC_INTERFACE
export interface ModelEvaluation {
  model_version: string;
  window_days: number;
  horizon_days: number;
  scores: number;
  equipment: number;
  model: WarningStats;
  threshold_alerts: WarningStats;
  notes: string[];
}

// PUBLIC_INTERFACE
export interface ModelDrift {
  model_version: string;
  window_days: number;
  status: 'stable' | 'moderate' | 'significant' | 'no_reference' | 'insufficient_data';
  samples?: number;
  score?: { psi: number; level: string };
  features: Record<string, { psi: number; level: string }>;
}

// PUBLIC_INTERFACE
export function listModels(signal?: AbortSignal): Promise<ModelVersion[]> {
  return apiRequest<ModelVersion[]>('/models', { signal });
}

// PUBLIC_INTERFACE
export function setModelStage(id: string, stage: ModelStage): Promise<ModelVersion> {
  return apiRequest<ModelVersion>(`/models/${encodeURIComponent(id)}/stage`, {
    method: 'POST',
    body: { stage },
  });
}

// PUBLIC_INTERFACE
export function getModelEvaluation(id: string, signal?: AbortSignal): Promise<ModelEvaluation> {
  return apiRequest<ModelEvaluation>(`/models/${encodeURIComponent(id)}/evaluation`, {
    signal,
    query: { days: 90, horizon_days: 7 },
  });
}

// PUBLIC_INTERFACE
export function getModelDrift(id: string, signal?: AbortSignal): Promise<ModelDrift> {
  return apiRequest<ModelDrift>(`/models/${encodeURIComponent(id)}/drift`, {
    signal,
    query: { days: 7 },
  });
}
