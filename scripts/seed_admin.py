"""Grant the Admin role to an existing Supabase Auth user (bootstrap).

Replaces the hard-coded admin grant that used to live in a schema migration.
The email comes from the environment, so no personal data is committed and
each environment (dev, staging, client production) chooses its own first
administrator. Further roles are managed in the app under Admin → Users.

Prerequisites:
- The schema is migrated (``alembic upgrade head`` or the baseline stamp).
- The user already exists in Supabase Auth (Dashboard → Authentication →
  Users → Add user / Invite). Passwords are set there, never here.

Usage:
    $env:DATABASE_URL = "postgresql+psycopg2://..."   # target environment
    $env:BOOTSTRAP_ADMIN_EMAIL = "admin@client.example"
    python scripts/seed_admin.py

It is idempotent: re-running it re-asserts the Admin role.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import get_settings  # noqa: E402

UPSERT = text(
    """
    insert into public.user_profiles (supabase_user_id, email, display_name,
                                      role)
    select id, email, coalesce(raw_user_meta_data->>'name', email), 'Admin'
    from auth.users
    where lower(email) = lower(:email)
    on conflict (supabase_user_id) do update
      set email = excluded.email,
          role = 'Admin',
          updated_at = now()
    returning supabase_user_id
    """
)


def main() -> int:
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip()
    if not email:
        print("Set BOOTSTRAP_ADMIN_EMAIL first.", file=sys.stderr)
        return 2

    engine = create_engine(get_settings().database_url)
    with engine.begin() as conn:
        if conn.execute(text("select to_regclass('auth.users')")).scalar():
            granted = conn.execute(UPSERT, {"email": email}).first()
        else:
            print("auth.users not found: not a Supabase database.", file=sys.stderr)
            return 1

    if granted is None:
        print(
            "No Supabase Auth user with that email. Create or invite the "
            "user in the Supabase dashboard first.",
            file=sys.stderr,
        )
        return 1
    print("Admin role granted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
