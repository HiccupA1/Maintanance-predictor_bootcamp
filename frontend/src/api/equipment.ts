import { apiRequest } from './client';
import type {
  Equipment,
  EquipmentListResponse,
  EquipmentPayload,
} from '../types/equipment';

/**
 * Equipment API adapter.
 *
 * TODO: The current backend has no Equipment router/schema. These calls use
 * the planned `/v1/equipment` contract so the UI is ready when that backend
 * slice is delivered; 404/401/403 responses are surfaced through ApiError.
 */

// PUBLIC_INTERFACE
export function listEquipment(signal?: AbortSignal): Promise<EquipmentListResponse> {
  /** Fetch all equipment records. */
  return apiRequest<EquipmentListResponse>('/equipment', { signal });
}

// PUBLIC_INTERFACE
export function getEquipment(
  equipmentId: string,
  signal?: AbortSignal,
): Promise<Equipment> {
  /** Fetch one equipment record by its public equipment identifier. */
  return apiRequest<Equipment>(
    `/equipment/${encodeURIComponent(equipmentId)}`,
    { signal },
  );
}

// PUBLIC_INTERFACE
export function createEquipment(payload: EquipmentPayload): Promise<Equipment> {
  /** Create an equipment record. The backend should enforce Admin authorization. */
  return apiRequest<Equipment>('/equipment', {
    method: 'POST',
    body: payload,
  });
}

// PUBLIC_INTERFACE
export function updateEquipment(
  equipmentId: string,
  payload: EquipmentPayload,
): Promise<Equipment> {
  /** Update an equipment record. The backend should enforce Admin authorization. */
  return apiRequest<Equipment>(
    `/equipment/${encodeURIComponent(equipmentId)}`,
    {
      method: 'PUT',
      body: payload,
    },
  );
}
