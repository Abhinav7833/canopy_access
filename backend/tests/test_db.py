from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

import app.core.db as db_module
from app.core.db import engine


def test_postgis_available():
    with engine.connect() as conn:
        version = conn.execute(text("SELECT postgis_version()")).scalar()
    assert version is not None and "3." in version


def test_get_db_commits_on_success(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(db_module, "SessionLocal", lambda: fake)
    gen = db_module.get_db()
    next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    fake.commit.assert_called_once()
    fake.close.assert_called_once()


def test_get_db_rolls_back_on_error(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(db_module, "SessionLocal", lambda: fake)
    gen = db_module.get_db()
    next(gen)
    with pytest.raises(ValueError):
        gen.throw(ValueError("boom"))
    fake.rollback.assert_called_once()
    fake.close.assert_called_once()
