from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.document import Document
from app.models.document_job import DocumentJob
from app.models.ocr_output import OCROutput
from app.models.page import Page
from app.services.document_processing import DocumentProcessingService
from app.services.engine_orchestrator import (
    EngineBinding, EngineOrchestrator, EngineRegistry, EngineSpec, default_orchestrator,
)
from app.services.ocr_engines.base import OCRAdapter
from tests.pdf_fixtures import write_pdf


class ExampleAdapter(OCRAdapter):
    engine_name = "example"

    async def parse(self, file_path: Path) -> dict:
        return {"engine": self.engine_name, "status": "completed", "raw_output": {"text": "Lesson"}}


def validate_example(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
        raise ValueError("Expected example text")


def normalize_example(result):
    return {"source": "example", "status": "completed", "pages": [
        {"page_number": 1, "raw_text": result["raw_output"]["text"]},
    ], "blocks": []}


def example_orchestrator():
    registry = EngineRegistry()
    registry.register(EngineBinding(
        EngineSpec("example", "general_ocr", ("pdf",)),
        ExampleAdapter(), validate_example, normalize_example,
    ))
    return EngineOrchestrator(registry)


def test_registry_rejects_duplicate_and_mismatched_names():
    orchestrator = example_orchestrator()
    binding = orchestrator.registry.require("example")
    with pytest.raises(ValueError, match="already registered"):
        orchestrator.registry.register(binding)
    with pytest.raises(ValueError, match="names differ"):
        EngineRegistry().register(EngineBinding(EngineSpec("wrong", "ocr", ("pdf",)), binding.adapter, validate_example, normalize_example))


def test_planner_keeps_unintegrated_engine_pending():
    orchestrator = default_orchestrator()
    profile = {"file_type": "png", "handwriting_score": 0.9}
    plan = orchestrator.plan(profile)
    assert plan.engine == "chandra"
    assert plan.status == "awaiting_engine"
    assert plan.max_attempts == 1
    with pytest.raises(ValueError, match="not registered"):
        orchestrator.plan(profile, "chandra")


def test_planner_checks_capabilities_and_manual_choice():
    orchestrator = example_orchestrator()
    plan = orchestrator.plan({"file_type": "pdf"}, "example")
    assert plan.status == "ready"
    assert plan.reason == "manual_selection"
    with pytest.raises(ValueError, match="does not support"):
        orchestrator.plan({"file_type": "png"}, "example")


@pytest.mark.anyio
async def test_executor_rejects_placeholder_and_wrong_engine(monkeypatch):
    orchestrator = example_orchestrator()
    plan = orchestrator.plan({"file_type": "pdf"}, "example")
    adapter = orchestrator.registry.require("example").adapter
    for result in ({"engine": "example", "status": "placeholder"}, {"engine": "other", "status": "completed"}):
        async def parse(_path):
            return result
        monkeypatch.setattr(adapter, "parse", parse)
        with pytest.raises(ValueError, match="envelope"):
            await orchestrator.execute(plan, Path("unused.pdf"))


@pytest.mark.anyio
async def test_executor_does_not_run_pending_plan():
    orchestrator = default_orchestrator()
    with pytest.raises(ValueError, match="not ready"):
        await orchestrator.execute(orchestrator.plan({"file_type": "png", "handwriting_score": 0.9}), Path("unused.png"))


def test_normalization_checks_common_contract_and_source():
    orchestrator = example_orchestrator()
    with pytest.raises(ValueError, match="Expected example"):
        orchestrator.normalize({"engine": "example", "raw_output": {}})
    binding = orchestrator.registry.require("example")
    registry = EngineRegistry()
    registry.register(EngineBinding(binding.spec, binding.adapter, validate_example,
                                    lambda result: {**normalize_example(result), "source": "wrong"}))
    with pytest.raises(ValueError, match="source"):
        EngineOrchestrator(registry).normalize({"engine": "example", "raw_output": {"text": "Lesson"}})


def test_new_engine_uses_existing_persistence_without_service_branch(db_session, tmp_path):
    orchestrator = example_orchestrator()
    class ExamplePolicy:
        def choose_engine(self, profile):
            return {"engine": "example", "reason": "test_policy"}
    orchestrator.router = ExamplePolicy()
    source = tmp_path / "lesson.pdf"
    write_pdf(source)
    document = Document(filename=source.name, file_type="pdf", storage_url=str(source), status="uploaded")
    db_session.add(document)
    db_session.flush()
    job = DocumentJob(document_id=document.id, status="queued")
    db_session.add(job)
    db_session.commit()
    DocumentProcessingService(db_session, orchestrator).run_pipeline(document.id, job.id, source)
    assert document.status == "parsed"
    assert job.status == "completed"
    output = db_session.scalars(select(OCROutput).where(OCROutput.document_id == document.id)).one()
    assert output.engine == "example"
    assert output.raw_output["_scanofy"]["orchestration"]["job_id"] == job.id
    assert document.router_decision["plan"]["policy_version"] == "routing-v1"
    assert db_session.scalars(select(Page).where(Page.document_id == document.id)).one().raw_text == "Lesson"
