# AGENTS.md

## Scope

These instructions apply to the entire `abdulbasit742/ML` repository.

Project: **ML Visual Site discovery baseline**. The only legacy product artifact is an opaque ZIP retained as inactive provenance.

## Source of truth

- `ml_project.json` is the machine-readable project, data, model, evaluation, risk, and deployment contract.
- `scripts/ml_project.py` owns validation and readiness semantics.
- `Kimi_Agent_ML Visual Site Build.zip` is read-only legacy evidence with Git blob SHA `1f61a8446ee478d4ee1331225b179035ccbc88e1`.
- Do not execute, edit in place, or mark the ZIP active.

## Commands

Use Python 3.11 or newer.

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/ml_project.py validate
python scripts/ml_project.py readiness --expect blocked
python scripts/repository_check.py
```

## Working rules

1. Preserve unknown values until supported by inspected source, data documentation, licenses, and evaluation evidence.
2. Keep deployment disabled until the project card is ready and an accountable risk reviewer is recorded.
3. Never commit real personal/sensitive datasets, secrets, populated environment files, or unreviewed serialized models.
4. Treat pickle/joblib/framework checkpoints and notebook outputs as untrusted executable or data artifacts.
5. Migrate archive contents only on a dedicated reviewed branch into normal text source with a lockfile and tests.
6. Do not present metrics, accuracy, fairness, safety, clinical, financial, employment, biometric, or production claims without cited evaluation evidence in the card.
7. Update tests, README, reference review, and security audit when the contract changes.

## Completion checklist

- Structural validation and tests pass.
- Repository check confirms the pinned archive is unchanged.
- Readiness result matches the evidence; do not weaken it for convenience.
- New data/model artifacts have provenance, license, privacy classification, and review.
- No deployment or external side effect occurs without explicit authorization.
