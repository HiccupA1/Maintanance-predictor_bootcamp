import {
  DEVELOPMENT_ROLES,
  getDevelopmentIdentity,
  setDevelopmentRole,
} from '../config/env';
import type { Role } from '../utils/rbac';

const ROLE_LABELS: Record<Role, string> = {
  Admin: 'Admin',
  PlantManager: 'Manager',
  Operator: 'Operator',
  MaintenanceEngineer: 'Engineer',
};

// PUBLIC_INTERFACE
export function DeveloperRoleSwitcher() {
  /**
   * Render a Vite-development-only persona selector.
   *
   * The selected role is persisted in local storage and the page reloads so
   * all data hooks and API requests use the newly selected identity.
   *
   * @returns A compact role button group in development, otherwise nothing.
   */
  if (!import.meta.env.DEV) return null;

  const activeRole = getDevelopmentIdentity().role;

  const selectRole = (role: Role) => {
    if (role === activeRole) return;
    setDevelopmentRole(role);
    window.location.reload();
  };

  return (
    <section
      aria-label="Development persona switcher"
      className="flex flex-wrap items-center gap-1 rounded-md border border-violet-200 bg-violet-50 p-1"
    >
      <span className="px-1 text-xs font-medium text-violet-800">Dev persona:</span>
      <div aria-label="Select development persona" className="flex flex-wrap gap-1" role="group">
        {DEVELOPMENT_ROLES.map((role) => (
          <button
            key={role}
            type="button"
            aria-pressed={role === activeRole}
            className={[
              'rounded px-2 py-1 text-xs font-medium transition',
              role === activeRole
                ? 'bg-violet-700 text-white'
                : 'text-violet-800 hover:bg-violet-100',
            ].join(' ')}
            onClick={() => selectRole(role)}
          >
            {ROLE_LABELS[role]}
          </button>
        ))}
      </div>
    </section>
  );
}
