"""Document-level orchestration; adapters own inference and raw formats."""
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.normalized import NormalizedDocument
from app.services.ocr_engines.base import OCRAdapter
from app.services.router import DocumentRouter


@dataclass(frozen=True)
class EngineSpec:
    name: str
    role: str
    input_types: tuple[str, ...]
    tasks: tuple[str, ...] = ("document_extraction",)
    scope: str = "document"


class EngineResult(BaseModel):
    """Engine-neutral envelope; raw formats remain adapter-owned."""
    model_config = ConfigDict(extra="allow")

    engine: str
    status: Literal["completed"]
    raw_output: dict
    markdown_output: str | None = None
    average_confidence: float | None = Field(default=None, ge=0, le=1)


@dataclass(frozen=True)
class EngineBinding:
    spec: EngineSpec
    adapter: OCRAdapter
    validate_raw: Callable[[dict], None]
    normalize: Callable[[dict], dict]


class EngineRegistry:
    def __init__(self):
        self._bindings: dict[str, EngineBinding] = {}

    def register(self, binding: EngineBinding) -> None:
        name = binding.spec.name
        if name in self._bindings:
            raise ValueError(f"Engine already registered: {name}")
        if name != binding.adapter.engine_name:
            raise ValueError("Engine spec and adapter names differ.")
        self._bindings[name] = binding

    def get(self, name: str) -> EngineBinding | None:
        return self._bindings.get(name)

    def specs(self) -> tuple[EngineSpec, ...]:
        return tuple(binding.spec for binding in self._bindings.values())

    def require(self, name: str) -> EngineBinding:
        binding = self.get(name)
        if binding is None:
            raise ValueError(f"Engine not registered: {name}")
        return binding


@dataclass(frozen=True)
class ExecutionPlan:
    engine: str
    reason: str
    input_type: str
    status: Literal["ready", "awaiting_engine"]
    task: str = "document_extraction"
    scope: str = "document"
    policy_version: str = "routing-v1"
    contract_version: str = "orchestration-v1"
    max_attempts: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


class EngineOrchestrator:
    def __init__(self, registry: EngineRegistry, router: DocumentRouter | None = None):
        self.registry = registry
        self.router = router or DocumentRouter()

    def plan(self, profile: dict, preferred_engine: str | None = None) -> ExecutionPlan:
        decision = self.router.choose_engine(profile) if preferred_engine is None else {
            "engine": preferred_engine, "reason": "manual_selection",
        }
        name = decision["engine"]
        binding = self.registry.get(name)
        input_type = profile["file_type"]
        if binding is None:
            if preferred_engine is not None:
                raise ValueError(f"Requested engine not registered: {name}")
            return ExecutionPlan(name, decision["reason"], input_type, "awaiting_engine")
        if input_type not in binding.spec.input_types or "document_extraction" not in binding.spec.tasks or binding.spec.scope != "document":
            raise ValueError(f"Engine {name} does not support document extraction for {input_type}.")
        return ExecutionPlan(name, decision["reason"], input_type, "ready")

    async def execute(self, plan: ExecutionPlan, file_path: Path) -> dict:
        if plan.status != "ready":
            raise ValueError("Execution plan is not ready.")
        binding = self.registry.require(plan.engine)
        result = await binding.adapter.parse(file_path)
        if not isinstance(result, dict) or result.get("engine") != plan.engine or result.get("status") != "completed":
            raise ValueError("Engine returned an invalid result envelope.")
        result = EngineResult.model_validate(result).model_dump()
        binding.validate_raw(result.get("raw_output"))
        return result

    def normalize(self, result: dict, *, validate_raw: bool = True) -> dict:
        binding = self.registry.require(result["engine"])
        if validate_raw:
            binding.validate_raw(result.get("raw_output"))
        normalized = NormalizedDocument.model_validate(binding.normalize(result)).model_dump()
        if normalized["source"] != result["engine"]:
            raise ValueError("Normalized source does not match the selected engine.")
        return normalized


def default_orchestrator() -> EngineOrchestrator:
    # Composition root: new engines are added here, not in the processing service.
    from app.services.normalizer import Normalizer
    from app.services.ocr_engines.mineru_adapter import MinerUAdapter

    registry = EngineRegistry()
    registry.register(EngineBinding(
        EngineSpec("mineru", "document_parsing", ("pdf", "docx")),
        MinerUAdapter(), MinerUAdapter.validate_output, Normalizer().normalize,
    ))
    return EngineOrchestrator(registry)
