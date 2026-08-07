import { useEffect, useState } from 'react';

import {
  createAdminUser,
  deleteAdminUser,
  updateAdminUser,
  type AdminUser,
} from '../../api/adminUsers';
import { Button } from '../../components/ui/Button';
import { ErrorPanel } from '../../components/ui/ErrorPanel';
import { RoleGate } from '../../components/RoleGate';
import type { Role } from '../../utils/rbac';

const ROLES: Role[] = ['Admin', 'PlantManager', 'Operator', 'MaintenanceEngineer'];

type AdminUserFormState = {
  supabase_user_id: string;
  email: string;
  display_name: string;
  role: Role;
};

const EMPTY_FORM: AdminUserFormState = {
  supabase_user_id: '',
  email: '',
  display_name: '',
  role: 'Operator',
};

// PUBLIC_INTERFACE
export function AdminUsersPage() {
  /** Admin-only interface for creating, editing, and deleting application profiles. */
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [form, setForm] = useState<AdminUserFormState>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState('');

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetchUsers();
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

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      if (editingId) {
        const updated = await updateAdminUser(editingId, {
          email: form.email.trim() ? form.email.trim() : null,
          display_name: form.display_name.trim() ? form.display_name.trim() : null,
          role: form.role,
        });
        setUsers((current) =>
          current.map((user) =>
            user.supabase_user_id === updated.supabase_user_id ? updated : user,
          ),
        );
        setMessage(`Updated ${updated.email ?? updated.supabase_user_id}.`);
      } else {
        const created = await createAdminUser({
          supabase_user_id: form.supabase_user_id.trim(),
          email: form.email.trim() ? form.email.trim() : null,
          display_name: form.display_name.trim() ? form.display_name.trim() : null,
          role: form.role,
        });
        setUsers((current) => [...current, created]);
        setMessage(`Added ${created.email ?? created.supabase_user_id}.`);
      }
      resetForm();
    } catch (requestError) {
      setError(requestError);
    } finally {
      setSaving(false);
    }
  };

  const edit = (user: AdminUser) => {
    setEditingId(user.supabase_user_id);
    setForm({
      supabase_user_id: user.supabase_user_id,
      email: user.email ?? '',
      display_name: user.display_name ?? '',
      role: user.role,
    });
  };

  const remove = async (user: AdminUser) => {
    if (!window.confirm(`Delete ${user.email ?? user.supabase_user_id}?`)) return;
    try {
      await deleteAdminUser(user.supabase_user_id);
      setUsers((current) =>
        current.filter((item) => item.supabase_user_id !== user.supabase_user_id),
      );
      setMessage(`Deleted ${user.email ?? user.supabase_user_id}.`);
    } catch (requestError) {
      setError(requestError);
    }
  };

  return (
    <RoleGate
      allowedRoles={['Admin']}
      fallback={
        <ErrorPanel
          title="Admin access required"
          error="Only administrators can manage users."
        />
      }
    >
      <div className="space-y-6">
        <header className="rounded-ui bg-gradient-to-r from-brand-700 to-brand-500 p-6 text-white shadow-card">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-100">
            Administration
          </p>
          <h1 className="mt-2 text-2xl font-semibold">Users & roles</h1>
        </header>

        {Boolean(error) && <ErrorPanel title="Unable to manage users" error={error} />}
        {message && (
          <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {message}
          </p>
        )}

        <form className="card grid gap-4 p-4 md:grid-cols-4" onSubmit={submit}>
          {!editingId && (
            <label className="label">
              Supabase user ID
              <input
                className="input"
                required
                value={form.supabase_user_id}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    supabase_user_id: event.target.value,
                  }))
                }
              />
            </label>
          )}
          <label className="label">
            Email
            <input
              className="input"
              type="email"
              value={form.email}
              onChange={(event) =>
                setForm((current) => ({ ...current, email: event.target.value }))
              }
            />
          </label>
          <label className="label">
            Display name
            <input
              className="input"
              value={form.display_name}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  display_name: event.target.value,
                }))
              }
            />
          </label>
          <label className="label">
            Role
            <select
              className="input"
              value={form.role}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  role: event.target.value as Role,
                }))
              }
            >
              {ROLES.map((role) => (
                <option key={role}>{role}</option>
              ))}
            </select>
          </label>
          <div className="flex gap-2 md:col-span-4">
            <Button type="submit" loading={saving}>
              {editingId ? 'Save changes' : 'Add user'}
            </Button>
            {editingId && (
              <Button type="button" variant="secondary" onClick={resetForm}>
                Cancel
              </Button>
            )}
          </div>
        </form>

        <section className="card overflow-hidden">
          <div className="card-header">
            <div>
              <h2 className="font-semibold text-slate-900">Application users</h2>
              <p className="mt-1 text-xs text-slate-500">
                Email and persisted application role.
              </p>
            </div>
            <Button variant="secondary" onClick={() => void loadUsers()} loading={loading}>
              Refresh
            </Button>
          </div>

          {loading ? (
            <div className="p-6 text-sm text-slate-500">Loading profiles…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left">Email</th>
                    <th className="px-4 py-3 text-left">Role</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((user) => (
                    <tr key={user.supabase_user_id}>
                      <td className="px-4 py-4">
                        <p className="font-medium text-slate-900">
                          {user.email || 'No email'}
                        </p>
                        <p className="text-xs text-slate-500">
                          {user.display_name || user.supabase_user_id}
                        </p>
                      </td>
                      <td className="px-4 py-4">{user.role}</td>
                      <td className="px-4 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="secondary" onClick={() => edit(user)}>
                            Edit
                          </Button>
                          <Button variant="danger" onClick={() => void remove(user)}>
                            Delete
                          </Button>
                        </div>
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

async function fetchUsers(): Promise<{ items: AdminUser[]; total: number }> {
  const { apiRequest } = await import('../../api/client');
  return apiRequest<{ items: AdminUser[]; total: number }>('/admin/users');
}
