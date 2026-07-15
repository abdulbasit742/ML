# Legacy archive provenance

- Path: `Kimi_Agent_ML Visual Site Build.zip`
- Added in commit: `02b5248b220c72cb98b3ca57d517fe88b358fef2`
- Git blob SHA: `1f61a8446ee478d4ee1331225b179035ccbc88e1`
- Active: **no**

The archive is retained as the original uploaded snapshot. Its contents are not represented as maintained source and must not be executed, deployed, imported into Python, or used to support performance claims.

`python scripts/repository_check.py` recalculates the Git blob ID in every CI run. A changed archive must be reviewed as a new binary artifact rather than silently accepted.

## Migration rule

A future source migration should preserve the ZIP until the extracted tree has been inventoried, licensed, scanned, tested, and compared against this pinned blob. The migration must use ordinary text files and an explicit dependency lock. It must not mark `legacy_archive.active` as true.
