from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers every table on Base.metadata
from app.api.v1 import documents as documents_api
from app.core.config import get_settings
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with testing_session() as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
async def client(
    db_session: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(settings, "mineru_output_dir", tmp_path / "mineru_outputs")
    monkeypatch.setattr(settings, "ocr_output_dir", tmp_path / "ocr_outputs")

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def skip_background_processing(*_args, **_kwargs) -> None:
        return None

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        documents_api,
        "run_document_processing",
        skip_background_processing,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()
