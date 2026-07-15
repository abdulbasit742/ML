# Changed-area security audit — 2026-07-15

## Controls added

- The legacy ZIP is pinned by its Git blob SHA and explicitly inactive.
- Deployment defaults to `disabled` and cannot become ready without documented task, users, data provenance/license/privacy, model schema/reproducibility, metrics/baseline, limitations, and risk review.
- Public/private endpoint declarations require HTTPS.
- Unreviewed pickle, joblib, PyTorch, ONNX, HDF5, and checkpoint files are rejected from tracked source.
- Tracked populated environment files, private keys, and common token shapes are rejected.
- Unknown fields and malformed metrics fail validation instead of being ignored.
- CI asserts that the current project remains honestly blocked until evidence changes.

## Residual risks

- The ZIP contents remain opaque and may contain vulnerable dependencies, secrets, unlicensed material, personal data, unsafe deserialization, or misleading ML claims.
- Git blob pinning proves archive identity, not archive safety.
- No model, dataset, source application, dependency lock, or evaluation result has been independently reviewed.
- No license file is present.

## Deployment gate

Do not extract into the default branch, deserialize model artifacts, process real data, publish a site, or expose an endpoint until the archive is migrated to reviewable source and `ml_project.json` passes readiness with evidence reviewed by an accountable owner.
