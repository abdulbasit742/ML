# ML Visual Site — discovery baseline

This repository currently contains one opaque legacy upload, `Kimi_Agent_ML Visual Site Build.zip`. It is retained unchanged for provenance but is **not an active application, model, dataset, or deployment**.

The maintained source is a dependency-free ML governance layer that makes unknowns explicit before any archive extraction or model activation:

- `ml_project.json` records purpose, data provenance, model inputs/outputs, evaluation evidence, risk review, and deployment state.
- `scripts/ml_project.py` validates the card, reports blockers, and fails readiness until evidence is complete.
- `scripts/repository_check.py` pins the legacy Git blob and rejects common secrets and unreviewed serialized-model artifacts.
- `tests/test_ml_project.py` covers fail-closed validation and readiness behavior.
- CI runs the same checks on Python 3.11, 3.12, and 3.13.

## Current status

`ml_project.json` is intentionally in `discovery` with deployment `disabled`. The card is structurally valid, but readiness is blocked because the archive's task, data sources, licenses, privacy classification, model framework, schemas, reproducibility, evaluation metrics, intended users, and risk review are not documented.

This is the correct state until those facts are verified. Do not change fields from `unknown` merely to make the readiness command pass.

## Commands

Requirements: Python 3.11 or newer and Git.

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/ml_project.py validate
python scripts/ml_project.py readiness --expect blocked
python scripts/ml_project.py report
python scripts/repository_check.py
```

When the project is genuinely ready, update the card with evidence and change CI's expected readiness from `blocked` to `ready` in the same reviewed change.

## Reviewing the legacy archive

Do not execute or import the ZIP directly. Review it on a dedicated branch or isolated machine:

1. verify the blob remains `1f61a8446ee478d4ee1331225b179035ccbc88e1`;
2. extract without following symlinks or overwriting repository files;
3. inventory source, licenses, dependencies, model files, datasets, network calls, and secrets;
4. migrate reviewable text source into normal repository paths;
5. document data and model provenance in `ml_project.json`;
6. add task-specific tests and evaluation evidence;
7. keep deployment disabled until independent risk review is recorded.

See [docs/archive-provenance.md](docs/archive-provenance.md), [docs/reference-review.md](docs/reference-review.md), and [docs/security-audit.md](docs/security-audit.md).

## License

No repository license is currently present. Do not assume permission to redistribute the legacy archive or future source.
