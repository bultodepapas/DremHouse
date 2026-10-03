# Current drawing aliases

**Status:** active publication index; source drawings retain their discipline status and authority<br>
**Version:** 1.25<br>
**Date:** 2026-08-21<br>
**Guide revision:** 0.4 — 2026-10-03; catalog version/date retained<br>
**Source:** [catalog](catalog.json), D-056, D-084, and the [coordination migration guide](../../docs/06_gestion_y_obra/connected_coordination_migration_and_extension_guide.md)<br>
**Construction authority:** none

This generated directory contains **27 stable SVG/PNG pairs**
representing the issues currently used for project coordination.

- [Open the visual drawing index](../README.md)
- [Inspect source-to-alias provenance and hashes](manifest.json)
- [Inspect the explicit promotion catalog](catalog.json)

Do not edit aliases directly. Issue and preserve the versioned drawing first, update its
catalog entry, and run `python3 .github/scripts/sync_current_drawings.py --write`.

“Current” does not mean frozen, approved, or suitable for construction. Every alias
inherits the status and limitations of its versioned source.

The [D-084 connected review](../../docs/06_gestion_y_obra/connected_coordination_workflow.md)
generates a separate candidate under `.build/coordination/` with eight SVG views, including
a GLZ-WS-A section projection only. Its findings do not replace these aliases. Optional
`--visuals` adds pinned-font PNG previews, contact sheets and pixel comparisons for review;
these do not approve a drawing. `drawing_inventory.json` records registered consumer
coverage and limitations. It is a migration ledger, not proof of full equivalence for all
27 published sheets. `actual/catalog.json` alone records explicit promotion of stable
aliases. `--release`, `--check-release`, `--rollback <release-id>` and `--watch` operate on
connected review packages and do not alter this alias set; rollback marks freshness as not
revalidated, and watch builds candidates only. Consumer-impact metadata accompanies a
complete rebuild. Current programme/workstation checks, unadopted equipment benchmark
geometry and ten structural plan-line comparisons remain bounded, with unsupported geometry
and engineering OPEN. The [increment 02 record](../../docs/06_gestion_y_obra/connected_coordination_increment_02.md)
and [source inventory](../../docs/06_gestion_y_obra/connected_source_inventory.md) record
the remaining consumer migration and known geometry gaps.
