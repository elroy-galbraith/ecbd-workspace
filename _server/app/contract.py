from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import yaml

VALID_BASES = {"repo", "run", "stage"}


class ContractError(Exception):
    """Raised when a stage contract is missing, malformed, or violated."""


class Access(str, Enum):
    READ = "read"
    READ_WRITE = "read-write"


@dataclass(frozen=True)
class InputSpec:
    path: str
    relative_to: str
    access: Access
    optional: bool = False

    @property
    def is_directory(self) -> bool:
        return self.path.endswith("/")


@dataclass(frozen=True)
class OutputSpec:
    path: str
    relative_to: str = "run"

    @property
    def is_directory(self) -> bool:
        return self.path.endswith("/")


@dataclass(frozen=True)
class StageContract:
    bootstrap: bool
    inputs: tuple[InputSpec, ...]
    outputs: tuple[OutputSpec, ...]
    prose: str


def _check_base(relative_to: str, path: str) -> None:
    if relative_to not in VALID_BASES:
        raise ContractError(
            f"invalid relative_to '{relative_to}' for '{path}' "
            f"(must be one of {sorted(VALID_BASES)})"
        )


def parse_contract(text: str) -> StageContract:
    if not text.startswith("---\n"):
        raise ContractError("CONTEXT.md is missing a frontmatter block")
    end = text.find("\n---", 4)
    if end == -1:
        raise ContractError("CONTEXT.md frontmatter block is not terminated")
    front_matter = text[4:end]
    prose = text[end + 4:].lstrip("\n")

    data = yaml.safe_load(front_matter) or {}
    if "inputs" not in data:
        raise ContractError("contract frontmatter is missing 'inputs'")
    if "outputs" not in data:
        raise ContractError("contract frontmatter is missing 'outputs'")

    inputs = []
    seen_access: dict[tuple[str, str], Access] = {}
    for item in data["inputs"]:
        _check_base(item["relative_to"], item["path"])
        access = Access(item["access"])
        key = (item["path"], item["relative_to"])
        if key in seen_access and seen_access[key] != access:
            raise ContractError(
                f"conflicting access levels declared for '{item['path']}' "
                f"(relative_to '{item['relative_to']}'): "
                f"'{seen_access[key].value}' vs '{access.value}'"
            )
        seen_access[key] = access
        inputs.append(
            InputSpec(
                path=item["path"],
                relative_to=item["relative_to"],
                access=access,
                optional=item.get("optional", False),
            )
        )

    outputs = []
    for item in data["outputs"]:
        relative_to = item.get("relative_to", "run")
        _check_base(relative_to, item["path"])
        outputs.append(OutputSpec(path=item["path"], relative_to=relative_to))

    return StageContract(
        bootstrap=bool(data.get("bootstrap", False)),
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        prose=prose,
    )
