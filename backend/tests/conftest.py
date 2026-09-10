import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.db import Base, get_db
from app.main import create_app

_engine = create_engine(get_settings().test_database_url, future=True)


def _ensure_test_database() -> None:
    """Create the test database if nothing else has (docker init / a prior run)."""
    base, _, dbname = get_settings().test_database_url.rpartition("/")
    admin = create_engine(f"{base}/postgres", isolation_level="AUTOCOMMIT", future=True)
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": dbname}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{dbname}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Iterator[None]:
    _ensure_test_database()
    with _engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    # Import models so every table is registered on Base.metadata.
    import app.models  # noqa: F401

    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def db_session() -> Iterator[Session]:
    conn = _engine.connect()
    txn = conn.begin()
    session = sessionmaker(bind=conn, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        txn.rollback()
        conn.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed(db_session: Session):
    """Return a callable that seeds a curated fixture into the test session."""
    from scripts.seed import _seed_methodologies, seed_project

    fixtures = Path(__file__).resolve().parents[2] / "seed_data" / "projects"

    def _seed(name: str = "nur_navoi_solar") -> str:
        _seed_methodologies(db_session)  # evidence.method_id FKs to methodologies
        return seed_project(db_session, json.loads((fixtures / f"{name}.json").read_text()))

    return _seed
