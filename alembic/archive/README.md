# Archived Alembic revisions (0002–0006)

**Not on the migration path.** Alembic only loads `alembic/versions/`.

This chain could not build a database. Revision `0001` had been deleted, so
`0002` altered a `work_orders` table that nothing created, and `0006` was
written afterwards to match the live database (D5). The single baseline
`alembic/versions/0001_baseline.py` replaces it (ADR-0009). These files are
kept so that the history of schema decisions is still reviewable.
