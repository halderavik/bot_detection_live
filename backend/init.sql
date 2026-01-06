-- Local Docker Postgres initialization
--
-- This file is mounted by docker-compose into `/docker-entrypoint-initdb.d/`
-- so it must exist on disk. The application creates tables on startup via
-- SQLAlchemy `Base.metadata.create_all`, so this can remain a no-op.
--
-- Reason: Prevent Docker Compose from creating a directory at this path when
-- the file is missing (which can break Postgres init scripts on some hosts).

