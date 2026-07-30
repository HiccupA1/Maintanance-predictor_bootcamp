import { Link } from 'react-router-dom';

import { EmptyState } from '../components/ui/EmptyState';

// PUBLIC_INTERFACE
export function NotFoundPage() {
  /** Fallback screen rendered for unknown routes. */
  return (
    <EmptyState
      title="Page not found"
      description="The page you requested does not exist."
      action={
        <Link
          to="/work-orders"
          className="rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Go to work orders
        </Link>
      }
    />
  );
}
