import { apiRequest } from './client';
import type { Role } from '../utils/rbac';

export interface AdminUser {
  id: string;
  supabase_user_id: string;
  email: string | null;
  display_name: string | null;
  role: Role;
}

export interface AdminUserPayload {
  email: string | null;
  display_name: string | null;
  role: Role;
}

export interface CreateAdminUserPayload extends AdminUserPayload {
  supabase_user_id: string;
}

// PUBLIC_INTERFACE
export function createAdminUser(
  payload: CreateAdminUserPayload,
): Promise<AdminUser> {
  /** Create an application profile for an existing Auth user. */
  return apiRequest<AdminUser>('/admin/users', {
    method: 'POST',
    body: payload,
  });
}

// PUBLIC_INTERFACE
export function updateAdminUser(
  supabaseUserId: string,
  payload: AdminUserPayload,
): Promise<AdminUser> {
  /** Update an application user's email, name, and role. */
  return apiRequest<AdminUser>(
    `/admin/users/${encodeURIComponent(supabaseUserId)}`,
    { method: 'PUT', body: payload },
  );
}

// PUBLIC_INTERFACE
export function deleteAdminUser(supabaseUserId: string): Promise<void> {
  /** Delete an application user profile. */
  return apiRequest<void>(
    `/admin/users/${encodeURIComponent(supabaseUserId)}`,
    { method: 'DELETE' },
  );
}
