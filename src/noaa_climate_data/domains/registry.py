"""Deterministic registry for publication domain dataset contracts."""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType

from . import (
    clouds_visibility,
    core_meteorology,
    precipitation,
    pressure_temperature,
    remarks,
    wind,
)


@dataclass(frozen=True)
class DomainDefinition:
    domain_name: str
    input_fields: tuple[str, ...]
    output_schema: tuple[tuple[str, str], ...]
    join_keys: tuple[str, ...]
    quality_rules: tuple[str, ...]


DOMAIN_MODULES: tuple[ModuleType, ...] = (
    core_meteorology,
    wind,
    precipitation,
    clouds_visibility,
    pressure_temperature,
    remarks,
)


def domain_definitions() -> tuple[DomainDefinition, ...]:
    definitions = tuple(_definition_from_module(module) for module in DOMAIN_MODULES)
    return tuple(sorted(definitions, key=lambda item: item.domain_name))


def domain_names() -> tuple[str, ...]:
    return tuple(definition.domain_name for definition in domain_definitions())


def _definition_from_module(module: ModuleType) -> DomainDefinition:
    domain_name = str(_require_attr(module, "DOMAIN_NAME"))
    input_fields = _normalize_text_tuple(_require_attr(module, "INPUT_FIELDS"))
    output_schema = _normalize_schema(_require_attr(module, "OUTPUT_SCHEMA"))
    join_keys = _normalize_text_tuple(_require_attr(module, "JOIN_KEYS"))
    quality_rules = _normalize_text_tuple(_require_attr(module, "QUALITY_RULES"))

    schema_columns = {column for column, _dtype in output_schema}
    missing_join_keys = [key for key in join_keys if key not in schema_columns]
    if missing_join_keys:
        raise ValueError(
            f"Domain {domain_name} has join keys missing from output schema: {missing_join_keys}"
        )

    return DomainDefinition(
        domain_name=domain_name,
        input_fields=input_fields,
        output_schema=output_schema,
        join_keys=join_keys,
        quality_rules=quality_rules,
    )


def _require_attr(module: ModuleType, attr_name: str) -> object:
    if not hasattr(module, attr_name):
        raise AttributeError(f"Missing required domain contract constant {attr_name}")
    return getattr(module, attr_name)


def _normalize_text_tuple(values: object) -> tuple[str, ...]:
    if isinstance(values, str):
        raise TypeError("Text tuple values must be an iterable, not a string")
    normalized = tuple(str(value) for value in values)  # type: ignore[arg-type]
    if not normalized:
        raise ValueError("Domain contract tuple values must not be empty")
    return normalized


def _normalize_schema(values: object) -> tuple[tuple[str, str], ...]:
    if isinstance(values, str):
        raise TypeError("Schema values must be an iterable, not a string")
    normalized: list[tuple[str, str]] = []
    for item in values:  # type: ignore[assignment]
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError("OUTPUT_SCHEMA entries must be 2-item tuples")
        column_name = str(item[0])
        dtype_name = str(item[1])
        if not column_name or not dtype_name:
            raise ValueError("OUTPUT_SCHEMA entries must include column name and dtype")
        normalized.append((column_name, dtype_name))
    if not normalized:
        raise ValueError("OUTPUT_SCHEMA must not be empty")
    return tuple(normalized)
