from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ml_project", ROOT / "scripts" / "ml_project.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)
BASE = json.loads((ROOT / "ml_project.json").read_text(encoding="utf-8"))


class ProjectCardTests(unittest.TestCase):
    def card(self):
        return copy.deepcopy(BASE)

    def ready_card(self):
        card = self.card()
        card["project"].update({
            "status": "ready", "owner": "ml-team", "task_type": "classification",
            "intended_users": ["researchers"], "decision_impact": "research support",
        })
        card["data"].update({
            "sources": [{"name": "demo", "uri": "data/demo.csv", "version": "v1", "license": "CC-BY-4.0"}],
            "provenance_status": "documented", "license_status": "approved",
            "contains_personal_data": False, "contains_sensitive_data": False,
            "split_strategy": "fixed train/validation/test split",
        })
        card["model"].update({
            "framework": "scikit-learn", "artifact_path": "models/model.bin",
            "training_code_path": "src/train.py", "input_schema": ["feature: float"],
            "output_schema": ["score: float"], "reproducible": True,
        })
        card["evaluation"].update({
            "metrics": [{"name": "accuracy", "value": 0.91, "threshold": 0.90, "direction": "higher", "dataset": "test-v1"}],
            "baseline": "majority class", "evaluation_dataset": "test-v1",
        })
        card["deployment"].update({"mode": "local", "rollback_plan": "disable local entrypoint"})
        card["risk"].update({
            "level": "low", "approved_uses": ["research demonstration"],
            "reviewer": "review-board", "reviewed_at": "2026-07-15T00:00:00Z",
        })
        return card

    def test_discovery_card_is_valid_but_blocked(self):
        result = module.validate_card(self.card())
        self.assertFalse(result.ready)
        self.assertIn("deployment is disabled", result.blockers)

    def test_unknown_top_level_field_is_rejected(self):
        card = self.card(); card["surprise"] = True
        with self.assertRaises(module.CardError): module.validate_card(card)

    def test_legacy_archive_must_remain_inactive(self):
        card = self.card(); card["legacy_archive"]["active"] = True
        with self.assertRaises(module.CardError): module.validate_card(card)

    def test_legacy_archive_blob_is_pinned(self):
        card = self.card(); card["legacy_archive"]["git_blob_sha"] = "0" * 40
        with self.assertRaises(module.CardError): module.validate_card(card)

    def test_ready_card_passes_readiness(self):
        self.assertTrue(module.validate_card(self.ready_card()).ready)

    def test_deployment_requires_ready_status(self):
        card = self.ready_card(); card["project"]["status"] = "development"
        self.assertIn("deployment requires ready project status", module.validate_card(card).blockers)

    def test_dataset_provenance_is_required(self):
        card = self.ready_card(); card["data"]["sources"] = []
        self.assertIn("dataset provenance is undocumented", module.validate_card(card).blockers)

    def test_personal_data_status_must_be_resolved(self):
        card = self.ready_card(); card["data"]["contains_personal_data"] = "unknown"
        self.assertIn("personal-data status is unknown", module.validate_card(card).blockers)

    def test_model_schemas_are_required(self):
        card = self.ready_card(); card["model"]["input_schema"] = []
        self.assertIn("model input/output schema is missing", module.validate_card(card).blockers)

    def test_metrics_are_required(self):
        card = self.ready_card(); card["evaluation"]["metrics"] = []
        self.assertIn("evaluation metrics are missing", module.validate_card(card).blockers)

    def test_metric_values_must_be_finite(self):
        card = self.ready_card(); card["evaluation"]["metrics"][0]["value"] = math.inf
        with self.assertRaises(module.CardError): module.validate_card(card)

    def test_public_endpoint_must_use_https(self):
        card = self.ready_card(); card["deployment"].update({"mode": "public", "endpoint": "http://example.com"})
        with self.assertRaises(module.CardError): module.validate_card(card)

    def test_report_exposes_blockers(self):
        report = module.render_report(module.validate_card(self.card()))
        self.assertIn("# ML Visual Site readiness report", report)
        self.assertIn("deployment is disabled", report)


if __name__ == "__main__":
    unittest.main()
