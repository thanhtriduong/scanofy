"""Engine-independent normalization boundary. Unknown evidence stays null."""
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BlockType = Literal["title", "heading", "paragraph", "list", "table", "image", "equation", "caption", "header", "footer", "page_number", "footnote", "reference", "unknown"]


class Geometry(BaseModel):
    bbox: list[float] | None = None
    coordinate_system: Literal["normalized_0_1"] | None = None

    @model_validator(mode="after")
    def check_coordinate_evidence(self):
        if (self.bbox is None) != (self.coordinate_system is None):
            raise ValueError("bbox and coordinate_system must both be present or both null")
        return self

    @field_validator("bbox", mode="before")
    @classmethod
    def validate_bbox(cls, value):
        if value is None:
            return None
        if not isinstance(value, list) or len(value) != 4 or not all(type(n) in (int, float) and math.isfinite(n) for n in value):
            raise ValueError("bbox must have four finite numbers")
        x0, y0, x1, y1 = value
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError("bbox must be ordered and normalized to 0..1")
        return value


class SpanData(Geometry):
    reading_order: int = Field(ge=0)
    span_type: str
    text: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    raw_json: dict = Field(default_factory=dict)


class PageData(BaseModel):
    page_number: int = Field(ge=1)
    width: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    height: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    image_url: str | None = None
    raw_text: str | None = None
    # Unknown until a source supplies verified page orientation.
    rotation: Literal[0, 90, 180, 270] | None = None


class BlockData(Geometry):
    page_number: int = Field(ge=1)
    block_type: BlockType
    text: str | None = None
    corrected_text: str | None = None
    reading_order: int = Field(ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_engine: str
    is_handwritten: bool | None = None
    needs_review: bool = False
    quality_score: float | None = Field(default=None, ge=0, le=1)
    heading_level: int | None = Field(default=None, ge=1)
    spans: list[SpanData] = Field(default_factory=list)
    raw_json: dict = Field(default_factory=dict)


class NormalizedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.1"] = "1.1"
    pages: list[PageData]
    blocks: list[BlockData]
    source: str
    status: str

    @model_validator(mode="after")
    def check_page_and_order(self):
        pages = {page.page_number for page in self.pages}
        if len(pages) != len(self.pages):
            raise ValueError("duplicate page number")
        keys = set()
        for block in self.blocks:
            key = (block.page_number, block.reading_order)
            if block.page_number not in pages or key in keys:
                raise ValueError("block references missing page or duplicate reading order")
            keys.add(key)
            if [span.reading_order for span in block.spans] != list(range(len(block.spans))):
                raise ValueError("span order must be contiguous within block")
        return self
