"""
Indexes the per-respondent queries need.

The tables were created before these lookups existed, and ``create_all`` never adds
an index to a table that already exists. Without them every final check scanned
whole tables (all events, all answers), so a burst of respondents finishing at once
pushed the database's CPU up and the final check past the tracker's 3 s wait.

``ensure_indexes`` runs in the background at startup. On PostgreSQL each index is
built with CREATE INDEX CONCURRENTLY, which does not block writes while it builds.
It logs which indexes it created and which already existed (under any name).
"""

from typing import List, Tuple

from sqlalchemy import text

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# (index name, table, columns)
INDEXES: List[Tuple[str, str, str]] = [
    ("idx_behavior_data_session", "behavior_data", "session_id"),
    ("idx_survey_responses_session", "survey_responses", "session_id"),
    ("idx_survey_responses_question", "survey_responses", "question_id"),
    ("idx_survey_questions_session", "survey_questions", "session_id"),
    ("idx_detection_results_session_created", "detection_results", "session_id, created_at"),
    ("idx_sessions_ip_survey", "sessions", "ip_address, survey_id"),
    ("idx_timing_analysis_session", "timing_analysis", "session_id"),
]


async def _covered(conn, table: str, columns: str) -> bool:
    """True when a valid index on exactly these leading columns already exists (any name)."""
    rows = await conn.execute(
        text(
            "SELECT pg_get_indexdef(i.indexrelid), i.indisvalid FROM pg_index i "
            "JOIN pg_class t ON t.oid = i.indrelid WHERE t.relname = :table"
        ),
        {"table": table},
    )
    wanted = f"({columns})"
    return any(valid and definition.endswith(wanted) for definition, valid in rows.all())


async def ensure_indexes(engine) -> dict:
    """Create the missing indexes. Returns {"created": [...], "existing": [...], "failed": [...]}."""
    report = {"created": [], "existing": [], "failed": []}
    postgres = engine.dialect.name == "postgresql"
    for name, table, columns in INDEXES:
        try:
            async with engine.connect() as conn:
                conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
                if postgres:
                    if await _covered(conn, table, columns):
                        report["existing"].append(name)
                        continue
                    # A concurrent build that failed earlier leaves an invalid index behind.
                    await conn.execute(text(f"DROP INDEX CONCURRENTLY IF EXISTS {name}"))
                    await conn.execute(text(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {table} ({columns})"))
                else:
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})"))
                report["created"].append(name)
        except Exception as error:  # noqa: BLE001 - a missing index slows queries, it must not stop the service
            report["failed"].append(name)
            logger.warning(f"Index {name} on {table} ({columns}) not created: {error}")
    logger.info(
        f"Database indexes: created {report['created'] or 'none'}; already there {report['existing'] or 'none'}; "
        f"failed {report['failed'] or 'none'}"
    )
    return report
