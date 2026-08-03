import { useMemo } from 'react';

import { EmptyState } from '../../components/ui/EmptyState';
import { RoleGate } from '../../components/RoleGate';
import type { Role } from '../../utils/rbac';

type UserRow = {
  id: string;
  email: string;
  role: Role;
  updated_at?: string | null;
};

const PLACEHOLDER_USERS: UserRow[] = [];

// PUBLIC_INTERFACE
export function AdminUsersPage() {
  /**
   * Admin-only user and role management screen.
   *
   * Step 1 provides the route + UI scaffold; Step 2 will wire this page to
   * backend endpoints that list users and update roles.
   */
  const users = useMemo(() => PLACEHOLDER_USERS, []);

  return (
    <RoleGate
      allowedRoles={['Admin']}
      fallback={
        <EmptyState
          title="Admin access required"
          description="You do not have permission to manage user roles."
        />
      }
    >
      <div className="space-y-4">
        <header>
          <h1 className="text-lg font-semibold text-slate-900">Users & Roles</h1>
          <p className="mt-1 text-sm text-slate-600">
            View application users and update their role assignments.
          </p>
        </header>

        {users.length === 0 ? (
          <EmptyState
            title="Role management is not yet connected"
            description="Backend role endpoints will be wired in Step 2. This page will list Supabase-authenticated users and allow Admins to update roles."
          />
        ) : (
          <section className="card overflow-hidden">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-700">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-slate-700">
                    Role
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-slate-700">
                    Last updated
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {users.map((u) => (
                  <tr key={u.id}>
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">
                      {u.email}
                    </td>
                    <td className="px-4 py-3 text-slate-700">{u.role}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {u.updated_at ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </div>
    </RoleGate>
  );
}
