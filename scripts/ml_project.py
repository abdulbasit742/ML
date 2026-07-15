#!/usr/bin/env python3
"""Validate and report the repository's ML project card without dependencies."""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

TOP_LEVEL = {
    "schema_version", "project", "data", "model", "evaluation",
    "deployment", "limitations", "risk", "legacy_archive",
}
STATUS = {"discovery", "development", "validation", "ready", "retired"}
UNKNOWN_BOOL = {True, False, "unknown"}
DEPLOYMENT_MODES = {"disabled", "local", "private", "public"}
RISK_LEVELS = {"unknown", "low", "medium", "high", "critical"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_ARCHIVE = "Kimi_Agent_ML Visual Site Build.zip"
EXPECTED_BLOB = "1f61a8446ee478d4ee1331225b179035ccbc88e1"


class CardError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    card: dict[str, Any]
    blockers: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.blockers


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CardError(f"{name} must be an object")
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise CardError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise CardError(f"{name} must not be empty")
    if len(value) > 500:
        raise CardError(f"{name} is too long")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise CardError(f"{name} must be a list")
    return value


def _iso_date(value: Any, name: str) -> str:
    value = _string(value, name)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CardError(f"{name} must be ISO-8601") from error
    return value


def _validate_metric(metric: Any, index: int) -> None:
    metric = _object(metric, f"evaluation.metrics[{index}]")
    required = {"name", "value", "threshold", "direction", "dataset"}
    if set(metric) != required:
        raise CardError(f"evaluation.metrics[{index}] must contain exactly {sorted(required)}")
    _string(metric["name"], f"evaluation.metrics[{index}].name")
    _string(metric["dataset"], f"evaluation.metrics[{index}].dataset")
    if metric["direction"] not in {"higher", "lower"}:
        raise CardError(f"evaluation.metrics[{index}].direction is invalid")
    for key in ("value", "threshold"):
        value = metric[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise CardError(f"evaluation.metrics[{index}].{key} must be finite")


def validate_card(raw: Any) -> ValidationResult:
    card = copy.deepcopy(_object(raw, "card"))
    if set(card) != TOP_LEVEL:
        missing = sorted(TOP_LEVEL - set(card))
        extra = sorted(set(card) - TOP_LEVEL)
        raise CardError(f"card keys mismatch; missing={missing}, extra={extra}")
    if card["schema_version"] != 1:
        raise CardError("schema_version must be 1")

    project = _object(card["project"], "project")
    data = _object(card["data"], "data")
    model = _object(card["model"], "model")
    evaluation = _object(card["evaluation"], "evaluation")
    deployment = _object(card["deployment"], "deployment")
    risk = _object(card["risk"], "risk")
    archive = _object(card["legacy_archive"], "legacy_archive")
    limitations = _list(card["limitations"], "limitations")

    for key in ("name", "owner", "purpose", "task_type", "decision_impact"):
        project[key] = _string(project.get(key), f"project.{key}")
    if project.get("status") not in STATUS:
        raise CardError("project.status is invalid")
    intended_users = _list(project.get("intended_users"), "project.intended_users")
    for index, value in enumerate(intended_users):
        _string(value, f"project.intended_users[{index}]")

    sources = _list(data.get("sources"), "data.sources")
    for index, source in enumerate(sources):
        source = _object(source, f"data.sources[{index}]")
        if set(source) != {"name", "uri", "version", "license"}:
            raise CardError(f"data.sources[{index}] must contain name, uri, version, license")
        for key in source:
            _string(source[key], f"data.sources[{index}].{key}")
    if data.get("provenance_status") not in {"missing", "partial", "documented"}:
        raise CardError("data.provenance_status is invalid")
    if data.get("license_status") not in {"unknown", "restricted", "approved"}:
        raise CardError("data.license_status is invalid")
    for key in ("contains_personal_data", "contains_sensitive_data"):
        if data.get(key) not in UNKNOWN_BOOL:
            raise CardError(f"data.{key} must be true, false, or unknown")
    _string(data.get("split_strategy"), "data.split_strategy")

    model["framework"] = _string(model.get("framework"), "model.framework")
    for key in ("artifact_path", "training_code_path"):
        if model.get(key) is not None:
            model[key] = _string(model[key], f"model.{key}")
            if model[key].startswith(("/", "../")) or "\\" in model[key]:
                raise CardError(f"model.{key} must be a safe repository-relative path")
    if not isinstance(model.get("reproducible"), bool):
        raise CardError("model.reproducible must be boolean")
    for key in ("input_schema", "output_schema"):
        values = _list(model.get(key), f"model.{key}")
        for index, value in enumerate(values):
            _string(value, f"model.{key}[{index}]")

    metrics = _list(evaluation.get("metrics"), "evaluation.metrics")
    for index, metric in enumerate(metrics):
        _validate_metric(metric, index)
    if evaluation.get("baseline") is not None:
        _string(evaluation["baseline"], "evaluation.baseline")
    if evaluation.get("evaluation_dataset") is not None:
        _string(evaluation["evaluation_dataset"], "evaluation.evaluation_dataset")
    if not isinstance(evaluation.get("subgroup_analysis"), bool):
        raise CardError("evaluation.subgroup_analysis must be boolean")

    if deployment.get("mode") not in DEPLOYMENT_MODES:
        raise CardError("deployment.mode is invalid")
    if deployment.get("endpoint") is not None:
        endpoint = _string(deployment["endpoint"], "deployment.endpoint")
        if not endpoint.startswith("https://"):
            raise CardError("deployment.endpoint must use HTTPS")
    if not isinstance(deployment.get("human_review_required"), bool):
        raise CardError("deployment.human_review_required must be boolean")
    if deployment.get("rollback_plan") is not None:
        _string(deployment["rollback_plan"], "deployment.rollback_plan")

    for index, limitation in enumerate(limitations):
        _string(limitation, f"limitations[{index}]")
    if risk.get("level") not in RISK_LEVELS:
        raise CardError("risk.level is invalid")
    for key in ("approved_uses", "prohibited_uses"):
        values = _list(risk.get(key), f"risk.{key}")
        for index, value in enumerate(values):
            _string(value, f"risk.{key}[{index}]")
    risk["reviewer"] = _string(risk.get("reviewer"), "risk.reviewer")
    if risk.get("reviewed_at") is not None:
        risk["reviewed_at"] = _iso_date(risk["reviewed_at"], "risk.reviewed_at")

    if archive.get("path") != EXPECTED_ARCHIVE:
        raise CardError("legacy_archive.path does not match the retained archive")
    if archive.get("git_blob_sha") != EXPECTED_BLOB or not SHA_RE.fullmatch(str(archive.get("git_blob_sha", ""))):
        raise CardError("legacy_archive.git_blob_sha does not match the reviewed blob")
    if archive.get("active") is not False:
        raise CardError("legacy_archive.active must remain false")

    blockers: list[str] = []
    def block(condition: bool, message: str) -> None:
        if condition:
            blockers.append(message)

    block(project["status"] != "ready", "project status is not ready")
    block(project["owner"] == "unassigned", "project owner is unassigned")
    block(project["task_type"] == "unknown", "ML task type is unknown")
    block(project["decision_impact"] == "unknown", "decision impact is unknown")
    block(not intended_users, "intended users are undocumented")
    block(data["provenance_status"] != "documented" or not sources, "dataset provenance is undocumented")
    block(data["license_status"] != "approved", "dataset license is not approved")
    block(data["contains_personal_data"] == "unknown", "personal-data status is unknown")
    block(data["contains_sensitive_data"] == "unknown", "sensitive-data status is unknown")
    block(data["split_strategy"] == "unknown", "dataset split strategy is unknown")
    block(model["framework"] == "unknown", "model framework is unknown")
    block(not model.get("artifact_path"), "model artifact path is missing")
    block(not model.get("training_code_path"), "training code path is missing")
    block(not model["input_schema"] or not model["output_schema"], "model input/output schema is missing")
    block(not model["reproducible"], "model is not marked reproducible")
    block(not metrics, "evaluation metrics are missing")
    block(not evaluation.get("baseline"), "evaluation baseline is missing")
    block(not evaluation.get("evaluation_dataset"), "evaluation dataset is missing")
    block(not limitations, "limitations are missing")
    block(risk["level"] == "unknown", "risk level is unknown")
    block(not risk["approved_uses"], "approved uses are missing")
    block(risk["reviewer"] == "unassigned" or not risk.get("reviewed_at"), "risk review is incomplete")
    block(deployment["mode"] == "disabled", "deployment is disabled")
    if deployment["mode"] != "disabled":
        block(project["status"] != "ready", "deployment requires ready project status")
        block(not deployment.get("rollback_plan"), "deployment rollback plan is missing")
        block(deployment["mode"] in {"private", "public"} and not deployment.get("endpoint"), "deployed endpoint is missing")

    return ValidationResult(card=card, blockers=tuple(dict.fromkeys(blockers)))


def load_card(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CardError(f"card not found: {path}") from error
    except json.JSONDecodeError as error:
        raise CardError(f"invalid JSON: {error}") from error


def render_report(result: ValidationResult) -> str:
    card = result.card
    project = card["project"]
    lines = [
        f"# {project['name']} readiness report", "",
        f"- Status: `{project['status']}`",
        f"- Deployment: `{card['deployment']['mode']}`",
        f"- Legacy archive active: `{str(card['legacy_archive']['active']).lower()}`",
        f"- Ready: `{str(result.ready).lower()}`", "", "## Blockers",
    ]
    lines.extend([f"- {item}" for item in result.blockers] or ["- None"])
    lines.extend(["", "## Limitations", *[f"- {item}" for item in card["limitations"]]])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate", "readiness", "report"))
    parser.add_argument("--card", type=Path, default=Path("ml_project.json"))
    parser.add_argument("--expect", choices=("ready", "blocked"))
    args = parser.parse_args(argv)
    try:
        result = validate_card(load_card(args.card))
    except CardError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.command == "validate":
        print("ML project card is structurally valid.")
        return 0
    if args.command == "report":
        print(render_report(result), end="")
        return 0
    actual = "ready" if result.ready else "blocked"
    print(f"ML project readiness: {actual}")
    for blocker in result.blockers:
        print(f"- {blocker}")
    if args.expect:
        return 0 if actual == args.expect else 2
    return 0 if result.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
