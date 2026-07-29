export type EquipmentHealthStatus = 'HEALTHY' | 'AT_RISK' | 'UNKNOWN' | string;

export interface Equipment {
  id: string;
  equipment_id: string;
  name: string;
  location: string;
  type: string;
  criticality: number;
  health_status?: EquipmentHealthStatus | null;
  last_service_date?: string | null;
  parameters?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface EquipmentListResponse {
  items: Equipment[];
  total?: number;
  page?: number;
  page_size?: number;
}

export interface EquipmentPayload {
  equipment_id: string;
  name: string;
  location: string;
  type: string;
  criticality: number;
}

export interface EquipmentFormValues {
  equipment_id: string;
  name: string;
  location: string;
  type: string;
  criticality: string;
}

export type EquipmentValidationErrors = Partial<
  Record<keyof EquipmentFormValues | 'form', string>
>;
