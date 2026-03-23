"""Validacao simples de cobertura minima para datasets unificados."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from common import load_json, resolve_repo_path


DEFAULT_BLADE_PATH = resolve_repo_path("data/unified/unified_blade.json")
DEFAULT_RUBBER_PATH = resolve_repo_path("data/unified/unified_rubber.json")


@dataclass(slots=True)
class CoverageRule:
    field_path: str
    minimum_ratio: float
    blocking: bool = True


COVERAGE_THRESHOLDS = {
    "blades": {
        "ratings.velocidade_revspin": 0.70,
        "ratings.controle_revspin": 0.70,
        "ratings.rigidez_revspin": 0.40,
    },
    "rubbers": {
        "meta.aprovado_larc": 1.00,
        "ratings.velocidade_revspin": 0.75,
        "ratings.spin_revspin": 0.75,
        "ratings.controle_revspin": 0.75,
    },
}


BLADE_RULES = [
    CoverageRule(field_path, minimum_ratio)
    for field_path, minimum_ratio in COVERAGE_THRESHOLDS["blades"].items()
]
BLADE_RULES += [
    CoverageRule("fisica.peso_g", 0.15, blocking=False),
    CoverageRule("composicao.total_camadas", 0.20, blocking=False),
]

RUBBER_RULES = [
    CoverageRule(field_path, minimum_ratio)
    for field_path, minimum_ratio in COVERAGE_THRESHOLDS["rubbers"].items()
]
RUBBER_RULES += [
    CoverageRule("fisica.espessuras_disponiveis_mm", 0.30, blocking=False),
]


def get_nested_value(record: dict, field_path: str):
    current = record
    for part in field_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def is_filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return True


def compute_field_coverage(records: list[dict], field_path: str) -> float:
    if not records:
        return 0.0
    filled = sum(1 for record in records if is_filled(get_nested_value(record, field_path)))
    return filled / len(records)


def validate_dataset(records: list[dict], rules: list[CoverageRule], label: str) -> tuple[list[str], list[str]]:
    report_lines: list[str] = []
    failures: list[str] = []

    report_lines.append(f"{label}: registros={len(records)}")
    for rule in rules:
        ratio = compute_field_coverage(records, rule.field_path)
        status = "OK" if ratio >= rule.minimum_ratio else ("WARN" if not rule.blocking else "FAIL")
        report_lines.append(
            f"  - {rule.field_path}: {ratio:.2%} (min {rule.minimum_ratio:.0%}) [{status}]",
        )
        if status == "FAIL":
            failures.append(f"{label}:{rule.field_path}:{ratio:.2%}<{rule.minimum_ratio:.0%}")

    return report_lines, failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida cobertura minima dos datasets unificados.")
    parser.add_argument("--blades", default=str(DEFAULT_BLADE_PATH), help="Caminho do unified_blade.json")
    parser.add_argument("--rubbers", default=str(DEFAULT_RUBBER_PATH), help="Caminho do unified_rubber.json")
    args = parser.parse_args()

    blade_records = load_json(Path(args.blades), default=[])
    rubber_records = load_json(Path(args.rubbers), default=[])

    blade_report, blade_failures = validate_dataset(blade_records, BLADE_RULES, "blades")
    rubber_report, rubber_failures = validate_dataset(rubber_records, RUBBER_RULES, "rubbers")

    for line in blade_report + rubber_report:
        print(line)

    failures = blade_failures + rubber_failures
    if failures:
        print("Resultado: cobertura minima do MVP nao atingida.")
        raise SystemExit(1)

    print("Resultado: cobertura minima do MVP atingida.")


if __name__ == "__main__":
    main()
