"""Parse YAML-backed fact objects without applying fact-type schema rules."""

from __future__ import annotations

from collections.abc import Mapping

from ruamel.yaml import YAML
from ruamel.yaml.constructor import SafeConstructor
from ruamel.yaml.nodes import ScalarNode

from ldvh.facts.models import CarrierParseResult, FactIssue

_TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"


class _JsonScalarConstructor(SafeConstructor):
    """Keep YAML timestamps as strings while retaining JSON scalar types."""

    yaml_constructors = SafeConstructor.yaml_constructors.copy()

    def construct_yaml_timestamp(self, node: ScalarNode) -> str:
        return self.construct_scalar(node)


_JsonScalarConstructor.add_constructor(_TIMESTAMP_TAG, _JsonScalarConstructor.construct_yaml_timestamp)


def _parse_issue(summary: str) -> CarrierParseResult:
    return CarrierParseResult(fields=None, body=None, issues=(FactIssue(category="parse", summary=summary),))


def parse_yaml_object(text: str) -> CarrierParseResult:
    """Parse one YAML mapping, reporting carrier failures as local parse issues."""

    yaml = YAML(typ="safe")
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    yaml.Constructor = _JsonScalarConstructor

    try:
        loaded = yaml.load(text)
    except Exception:  # ruamel exposes several parser, composer, and constructor errors
        return _parse_issue("事实对象无法按 YAML 1.2 唯一解析")

    if not isinstance(loaded, Mapping):
        return _parse_issue("YAML 事实对象顶层必须是映射")

    return CarrierParseResult(fields=dict(loaded), body=None)
