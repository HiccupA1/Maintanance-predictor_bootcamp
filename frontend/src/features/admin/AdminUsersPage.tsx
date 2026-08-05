import { useEffect, useState } from 'react';

import { apiRequest } from '../../api/client';
import { Button } from '../../components/ui/Button';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { RoleGate } from '../../components/RoleGate';
import type { Role } from '../../utils/rbac';

type UserRow = {
  id: string;
  supabase_user_id: string;
  email: string | null;
  display_name: string | null;
  role: Role;
};

type UsersResponse = {
  items: UserRow[];
  total: number;
};

const ROLES: Role[] = [
  'Admin',
  'PlantManager',
  'Operator',
  'MaintenanceEngineer',
];

// PUBLIC_INTERFACE
export function AdminUsersPage() {
  /** Admin-only screen for reviewing profiles and assigning application roles. */
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState('');

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await apiRequest<UsersResponse>('/admin/users');
      setUsers(response.items);
      setError(null);
    } catch (requestError) {
      setError(requestError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const updateRole = async (user: UserRow, role: Role) => {
    setSavingId(user.supabase_user_id);
    setMessage('');
    try {
      const updated = await apiRequest<UserRow>(
        `/admin/users/${encodeURIComponent(user.supabase_user_id)}/role`,
        { method: 'PUT', body: { role } },
      );
      setUsers((current) =>
        current.map((item) =>
          item.supabase_user_id === updated.supabase_user_id ? updated : item,
        ),
      );
      setMessage(`Updated ${updated.email ?? 'user'} to ${role}.`);
    } catch (requestError) {
      setError(requestError);
    } finally {
      setSavingId(null);
    }
  };

  return (
    <RoleGate allowedRoles={['Admin']} fallback={<ErrorPanel title="Admin access required" error="Only administrators can manage users." />}>
      <div className="space-y-6">
        <header className="rounded-ui bg-gradient-to-r from-brand-700 to-brand-500 p-6 text-white shadow-card">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-100">Administration</p>
          <h1 className="mt-2 text-2xl font-semibold">Users & roles</h1>
          <p className="mt-2 max-w-2xl text-sm text-brand-50">
            Review users created through Supabase Auth and assign the application role
            that controls their workspace.
          </p>
        </header>

        {error && <ErrorPanel title="Unable to load users" error={error} />}
        {message && <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</p>}

        <section className="card overflow-hidden">
          <div className="card-header">
            <div>
              <h2 className="font-semibold text-slate-900">Application users</h2>
              <p className="mt-1 text-xs text-slate-500">
                New authenticated users are created as Operators by default.
              </p>
            </div>
            <Button variant="secondary" onClick={() => void loadUsers()} loading={loading}>
              Refresh
            </Button>
          </div>

          {loading ? (
            <div className="p-6 text-sm text-slate-500">Loading profiles…</div>
          ) : users.length === 0 ? (
            <div className="p-6 text-sm text-slate-500">
              No profiles exist yet. Create users in Supabase Auth, then have them sign
              in once so their profiles are provisioned here.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">User</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Role</th>
                    <th className="px-4 py-3 text-right font-medium text-slate-600">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {users.map((user) => (
                    <tr key={user.supabase_user_id}>
                      <td className="px-4 py-4">
                        <p className="font-medium text-slate-900">{user.display_name || 'Unnamed user'}</p>
                        <p className="text-xs text-slate-500">{user.email || 'No email'}</p>
                      </td>
                      <td className="px-4 py-4">
                        <select
                          className="input mt-0 max-w-xs"
                          value={user.role}
                          disabled={savingId === user.supabase_user_id}
                          onChange={(event) => void updateRole(user, event.target.value as Role)}
                          aria-label={`Role for ${user.email || user.supabase_user_id}`}
                        >
                          {ROLES.map((role) => <option key={role}>{role}</option>)}
                        </select>
                      </td>
                      <td className="px-4 py-4 text-right text-xs text-slate-500">
                        {savingId === user.supabase_user_id ? 'Saving…' : 'Saved automatically'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </RoleGate>
  );
}
