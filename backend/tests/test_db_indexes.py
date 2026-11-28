"""The indexes the per-respondent queries need are created at startup, and creating them twice is harmless."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401 - registers the tables
from app.database import Base
from app.db_indexes import INDEXES, ensure_indexes


@pytest.mark.asyncio
async def test_missing_indexes_are_created_once(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'idx.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    first = await ensure_indexes(engine)
    assert first["failed"] == [] and sorted(first["created"]) == sorted(name for name, _, _ in INDEXES)
    async with engine.connect() as conn:
        names = {row[0] for row in (await conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))).all()}
    assert {name for name, _, _ in INDEXES} <= names
    assert (await ensure_indexes(engine))["failed"] == []  # running again changes nothing
    await engine.dispose()
