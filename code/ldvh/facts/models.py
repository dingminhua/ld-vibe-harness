"""Small immutable values shared by fact-object carrier and validation modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

IssueCategory = Literal[
    "location",
    "git-traceability",
    "parse",
    "schema",
    "identity",
    "reference",
    "relation",
]


@dataclass(frozen=True, slots=True)
class FactIssue:
    category: IssueCategory
    summary: str
    code: str | None = None
    field_path: str | None = None


@dataclass(frozen=True, slots=True)
class CarrierParseResult:
    fields: dict[str, Any] | None
    body: str | None
    issues: tuple[FactIssue, ...] = ()

    @property
    def parsed(self) -> bool:
        return self.fields is not None and not self.issues


@dataclass(frozen=True, slots=True)
class FactReference:
    governed_project_id: str
    fact_type_key: str
    object_id: str

    def to_json(self) -> dict[str, str]:
        return {
            "governed_project_id": self.governed_project_id,
            "fact_type_key": self.fact_type_key,
            "object_id": self.object_id,
        }


@dataclass(frozen=True, slots=True)
class FactReferenceScope:
    fact_ref_index: int
    requested_ref: FactReference

    def to_json(self) -> dict[str, object]:
        return {"fact_ref_index": self.fact_ref_index, "requested_ref": self.requested_ref.to_json()}
