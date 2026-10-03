"""Build, inspect, and verify isolated, complete coordination review packages."""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from dreamhouse.coordination.capabilities import capability_report
from dreamhouse.coordination.dependencies import dependency_report
from dreamhouse.coordination.drawings import render_drawings
from dreamhouse.coordination.evidence import assess_evidence
from dreamhouse.coordination.information_requirements import information_requirements
from dreamhouse.coordination.model import (
    DEFAULT_PROJECT,
    ROOT,
    CoordinationError,
    dependency_hashes,
    digest,
    file_hash,
    json_text,
    read_json,
    resolve_project,
    study_template,
)
from dreamhouse.coordination.navigation import attach_navigation
from dreamhouse.coordination.phase_gates import gate_markdown, phase_gate_record
from dreamhouse.coordination.reader import attach_reading_guide, companion_pages
from dreamhouse.coordination.render import render_views
from dreamhouse.coordination.rules import evaluate
from dreamhouse.coordination.view_contract import compare_anchors, inspect_views
from dreamhouse.coordination.viewpoints import build_viewpoints
from dreamhouse.coordination.visual_quality import visual_quality_report
from dreamhouse.cost.reconcile import reconcile_costs

DEFAULT_OUTPUT = ROOT / ".build/coordination"
REQUIRED_VIEW_FILES = {
    "plan-pb.svg",
    "plan-p2.svg",
    "elevation-side-a.svg",
    "elevation-side-b.svg",
    "elevation-front.svg",
    "elevation-rear.svg",
    "window-details.svg",
    "window-sections.svg",
    "stair-sections.svg",
    "index.html",
}


def _output_directory(out: Path) -> Path:
    out = Path(out).resolve()
    if ROOT.is_relative_to(out) or (
        out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / ".build")
    ):
        raise CoordinationError("Choose an isolated output under .build/ or outside the repository")
    return out


@contextmanager
def _build_lock(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".build.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield


def _safe_relative(name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or str(path) == ".":
        raise CoordinationError(f"Unsafe artifact path: {name}")
    return path


def _verify_package(issue: Path) -> dict:
    if issue.is_symlink() or any(path.is_symlink() for path in issue.rglob("*")):
        raise CoordinationError("Review package contains substituted symbolic links")
    manifest = read_json(issue / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("build_status") != "complete":
        raise CoordinationError("Review package is incomplete")
    files = manifest.get("artifacts", {})
    if not files or not isinstance(files, dict):
        raise CoordinationError("Review package has no artifact inventory")
    actual = {p.relative_to(issue).as_posix() for p in issue.rglob("*") if p.is_file()} - {
        "manifest.json"
    }
    if actual != set(files):
        raise CoordinationError("Review artifact inventory differs from its manifest")
    for name, expected in files.items():
        path = issue / _safe_relative(name)
        if path.is_symlink() or file_hash(path) != expected:
            raise CoordinationError(f"Changed or substituted generated artifact: {name}")
    return manifest


def _write_pointer(out: Path, payload: dict) -> None:
    fd, name = tempfile.mkstemp(prefix=".latest-", suffix=".json", dir=out)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json_text(payload))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, out / "latest.json")
    finally:
        Path(name).unlink(missing_ok=True)


def view_inventory(snapshot: dict, files: dict[str, str]) -> dict:
    """Validate generated occurrences, anchors, dimensions and cross-view references."""
    return inspect_views(snapshot, files)


def _visual_configuration(width_px: int) -> dict:
    from dreamhouse.coordination.visual import visual_configuration

    return visual_configuration(_font_paths(), width_px=width_px)


def _font_paths() -> tuple[Path, ...]:
    root = Path(__file__).with_name("fonts")
    return tuple(root / name for name in ("IBMPlexSans-Regular.ttf", "IBMPlexSans-Bold.ttf"))


def _issue_identity(input_hash: str, rendering: dict | None) -> str:
    return digest({"source_input_hash": input_hash, "rendering": rendering, "package_schema": 3})


def _render_outputs(snapshot: dict, result: dict) -> tuple[dict, dict]:
    files = render_views(snapshot, result)
    missing_views = REQUIRED_VIEW_FILES - set(files)
    if missing_views:
        raise CoordinationError(f"Renderer omitted required review views: {sorted(missing_views)}")
    migrated = render_drawings(snapshot, result)
    expected_drawings = {
        f"drawings/{item['id']}.svg" for item in snapshot["drawing_catalog"]["drawings"]
    } | {"drawings/index.html"}
    if set(migrated["files"]) != expected_drawings:
        raise CoordinationError("Renderer omitted or substituted required catalog drawings")
    duplicates = set(files).intersection(migrated["files"])
    if duplicates:
        raise CoordinationError(f"Drawing artifacts collide: {sorted(duplicates)}")
    files.update(migrated["files"])
    files["structural_screening.json"] = json_text(migrated["structural_screening"])
    files["index.html"] = files["index.html"].replace(
        "</body>",
        '<section aria-label="Connected drawing catalog"><h2>Connected drawing catalog</h2>'
        '<p><a href="drawings/index.html">Open all catalog drawing consumers</a> · '
        '<a href="drawing_inventory.json">Migration coverage and limitations</a> · '
        '<a href="extensions.json">Wall, stair, service and maintenance evidence</a> · '
        '<a href="structural_screening.json">Structural screening hypotheses and results</a></p>'
        "</section></body>",
    )
    files["visual_quality.json"] = json_text(visual_quality_report(files, snapshot))
    files.update(companion_pages(files, snapshot))
    files["index.html"] = attach_reading_guide(files["index.html"], files)
    return files, migrated["inventory"]


def _review_text(snapshot: dict, result: dict, cost: dict, files: dict) -> str:
    findings = result["findings"]
    counts = {
        status: sum(f["status"] == status for f in findings) for status in ("PASS", "OPEN", "FAIL")
    }
    lines = [
        "# Connected coordination review",
        "",
        "**Version:** 0.3  ",
        "**Format date:** 2026-10-03  ",
        "**Status:** complete coordination candidate; not construction authority  ",
        "**Source:** PB b37, P2 b28, SC-01, rooflight b12 and explicit repository study changes  ",
        f"**Scenario:** {snapshot['scenario_id']}  ",
        f"**Input fingerprint:** `{snapshot['input_hash']}`",
        "",
        f"Findings: {counts['PASS']} PASS, {counts['OPEN']} OPEN, {counts['FAIL']} FAIL.",
        "",
        "Open the [read-only review](index.html). Geometry is authored in the source JSON study; SVG is generated output.",
        "",
        "A complete build means the listed artifacts were produced together. It does not mean that engineering checks, procurement or construction are approved.",
        "",
        "See [phase gate evidence](phase_gates.md), [saved issue viewpoints](viewpoints.json), [purpose-specific information](information_requirements.json) and [review evidence freshness](evidence.json).",
        "",
        "## Coverage and authority",
        "",
        "Facade windows, rooflight plan extents, located doors, P2 spaces, PB core spaces, shared stair and column reservations have persistent identities. Host planes and inferred room boundaries do not establish wall assemblies. Door heights, several PB door anchors, column vertical extents, engineering design and professional approvals remain unresolved.",
        "",
        "The [connected drawing catalog](drawings/index.html) regenerates registered consumers from this snapshot and records their scope in [drawing inventory](drawing_inventory.json). Historical adopted aliases retain their original authority. A review release is not a new architectural adoption; see [rule coverage](coverage.json).",
        "",
        "All affected opening/host and opening/column candidates are recomputed; no incremental result reuse is claimed. Unresolved geometry yields pending coverage, never an assertion of clearance.",
        "",
        "Current programme and equipment benchmark checks are connected to the captured source context. Read [discipline evidence](disciplines.json) for applicability and unknown engineering inputs. Historical placement hypotheses are not selected equipment layouts.",
        "",
        "The [house extension evidence](extensions.json) connects supported wall-line measurements, stair levels, phase/service reservations and maintenance requirements. Unknown surface areas, masses, products, routes and commissioning evidence remain explicitly unevaluated.",
        "",
        "Named dimensions and cross-view callouts are audited in [view inventory](view_inventory.json); [anchor changes](anchor_lifecycle.json) and [consumer dependencies](dependencies.json) expose propagation and outstanding professional review obligations.",
        "",
        f"Cost reconciliation retains {len(cost['open_or_ineligible_assemblies'])} open/ineligible assemblies; approved budget total remains null.",
        "",
        "## Review artifacts",
        "",
    ]
    lines += [
        f"- [{name}]({name})" for name in sorted(files) if name.endswith((".svg", ".json", ".png"))
    ]
    lines += ["", "## Findings requiring attention", ""]
    for finding in findings:
        if finding["status"] != "PASS":
            ids = ", ".join(finding.get("entity_ids", [])) or "project"
            lines.append(
                f"- **{finding['status']} · {finding['rule_id']} · {ids}:** {finding['message']}"
            )
    return "\n".join(lines) + "\n"


def build_candidate(
    project_path: Path = DEFAULT_PROJECT,
    out: Path = DEFAULT_OUTPUT,
    *,
    visuals: bool = False,
    visual_width_px: int = 1400,
) -> dict:
    """Write a full candidate atomically; failure leaves the previous pointer unchanged.

    Serialize writers for this output root and recheck inputs before pointer replacement.
    A source edit after replacement makes the package stale; `check_candidate` detects it.
    """
    out = _output_directory(out)
    with _build_lock(out):
        snapshot = resolve_project(project_path)
        rendering = _visual_configuration(visual_width_px) if visuals else None
        baseline = dict(
            snapshot,
            **snapshot["baseline"],
            model_hash=snapshot["base_model_hash"],
            scenario_id="ARCHIVED_CURRENT_BASELINE",
            changes_requested={},
        )
        result = evaluate(snapshot, baseline)
        cost = reconcile_costs(
            result["quantity_ledger"],
            mapping=read_json(ROOT / "dreamhouse/cost/cost_mapping.json"),
            rate_book=read_json(ROOT / "dreamhouse/cost/rate_book.json"),
        )
        files, drawing_inventory = _render_outputs(snapshot, result)
        inventory = view_inventory(snapshot, files)
        viewpoints = build_viewpoints(snapshot, result, inventory)
        files["viewpoints.json"] = json_text(viewpoints)
        files["index.html"] = attach_navigation(
            files["index.html"], snapshot, inventory, viewpoints=viewpoints
        )
        files["capabilities.json"] = json_text(
            capability_report(snapshot, result, inventory, drawing_inventory)
        )
        baseline_views, _ = _render_outputs(baseline, evaluate(baseline))
        baseline_inventory = view_inventory(baseline, baseline_views)
        files["view_inventory.json"] = json_text(inventory)
        files["anchor_lifecycle.json"] = json_text(compare_anchors(inventory, baseline_inventory))
        files["dependencies.json"] = json_text(dependency_report(snapshot, result, inventory))
        files["evidence.json"] = json_text(assess_evidence(snapshot))
        files["information_requirements.json"] = json_text(
            information_requirements(snapshot, result)
        )
        for name, value in {
            "model.json": snapshot,
            "findings.json": result["findings"],
            "coverage.json": result["coverage"],
            "disciplines.json": result["disciplines"],
            "extensions.json": result["extensions"],
            "changes.json": result["changes"],
            "finding_lifecycle.json": result["finding_lifecycle"],
            "openings.json": result["opening_schedule"],
            "quantities.json": result["quantity_ledger"],
            "cost.json": cost,
            "drawing_inventory.json": drawing_inventory,
        }.items():
            files[name] = json_text(value)
        if visuals:
            from dreamhouse.coordination.visual import compare_visuals, render_visuals

            previews, visual_manifest = render_visuals(
                {name: value for name, value in files.items() if name.endswith(".svg")},
                font_paths=_font_paths(),
                width_px=visual_width_px,
            )
            baseline_previews, baseline_visual_manifest = render_visuals(
                {name: value for name, value in baseline_views.items() if name.endswith(".svg")},
                font_paths=_font_paths(),
                width_px=visual_width_px,
            )
            differences, comparison = compare_visuals(
                previews,
                baseline_previews,
                current_configuration=visual_manifest["configuration"],
                baseline_configuration=baseline_visual_manifest["configuration"],
            )
            comparison.update(
                baseline_scenario_id=baseline["scenario_id"],
                baseline_model_hash=baseline["model_hash"],
                current_scenario_id=snapshot["scenario_id"],
                current_model_hash=snapshot["model_hash"],
                includes_sheet_metadata=True,
                interpretation="Pixel changes include scenario labels and findings, not just geometry; review them with changes.json and anchor_lifecycle.json. No automatic visual acceptance threshold.",
            )
            if _visual_configuration(visual_width_px) != rendering:
                raise CoordinationError("Visual configuration changed during rendering")
            files.update(previews)
            files.update(differences)
            files.update({f"baseline/{name}": value for name, value in baseline_previews.items()})
            files.update(
                {
                    f"baseline/{name}": value
                    for name, value in baseline_views.items()
                    if name.endswith(".svg")
                }
            )
            files["baseline/visual_manifest.json"] = json_text(baseline_visual_manifest)
            files["visual_manifest.json"] = json_text(visual_manifest)
            files["visual_comparison.json"] = json_text(comparison)
            files["index.html"] = files["index.html"].replace(
                "</body>",
                '<section aria-label="Visual exports"><h2>Visual exports</h2>'
                '<p><a href="contact_sheet.png">Open the PNG contact sheet</a> · '
                '<a href="baseline/contact_sheet.png">Archived baseline contact sheet</a> · '
                '<a href="visual_manifest.json">Rendering provenance</a> · '
                '<a href="visual_comparison.json">Baseline pixel comparison</a></p>'
                "<p>Pixel differences include scenario labels and findings; they are review "
                "evidence, not design approval.</p></section></body>",
            )
        gates = phase_gate_record(
            snapshot, inventory, drawing_inventory, set(files) | {"review.md"}
        )
        if any(row["missing_artifacts"] for row in gates["subphases"]):
            raise CoordinationError("Incomplete phase gate artifacts; candidate was not published")
        files["phase_gates.json"] = json_text(gates)
        files["phase_gates.md"] = gate_markdown(gates)
        files["review.md"] = _review_text(snapshot, result, cost, files)
        issue_id = _issue_identity(snapshot["input_hash"], rendering)
        issues = out / "issues"
        issues.mkdir(exist_ok=True)
        target = issues / issue_id
        stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=out))
        try:
            for name, contents in files.items():
                path = stage / _safe_relative(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(contents, bytes):
                    path.write_bytes(contents)
                else:
                    path.write_text(contents, encoding="utf-8")
            manifest = {
                "schema_version": 3,
                "build_status": "complete",
                "purpose": "coordination review",
                "scenario_id": snapshot["scenario_id"],
                "issue_id": issue_id,
                "input_hash": snapshot["input_hash"],
                "rendering": rendering,
                "model_hash": snapshot["model_hash"],
                "hash_policy": snapshot["hash_policy"],
                "font_policy": "Pinned local fonts and recorded renderer environment for PNG"
                if visuals
                else "SVG text uses viewer font fallbacks; pixel equivalence is not certified",
                "engineering_approval": False,
                "construction_authority": False,
                "published_aliases_promoted": False,
                "check_status": "FAIL"
                if any(f["status"] == "FAIL" for f in result["findings"])
                else "OPEN",
                "artifacts": {name: file_hash(stage / name) for name in sorted(files)},
            }
            (stage / "manifest.json").write_text(json_text(manifest), encoding="utf-8")
            _verify_package(stage)
            source_path = Path(snapshot["project_path"])
            if not source_path.is_absolute():
                source_path = ROOT / source_path
            if dependency_hashes(source_path) != snapshot["build_dependencies"]:
                raise CoordinationError(
                    "Inputs changed during generation; candidate was not published"
                )
            if target.exists():
                existing = _verify_package(target)
                if existing != manifest:
                    raise CoordinationError(
                        "Same input fingerprint produced different artifacts; inspect determinism"
                    )
            else:
                os.replace(stage, target)
            _write_pointer(
                out,
                {
                    "schema_version": 1,
                    "issue_id": issue_id,
                    "manifest_sha256": file_hash(target / "manifest.json"),
                },
            )
            return {"path": str(target), "manifest": manifest}
        finally:
            if stage.exists():
                shutil.rmtree(stage)


def check_candidate(
    project_path: Path = DEFAULT_PROJECT,
    out: Path = DEFAULT_OUTPUT,
    *,
    visuals: bool | None = None,
) -> dict:
    """Verify the whole artifact set and its full current dependency fingerprint."""
    out = _output_directory(out)
    if not (out / "latest.json").is_file():
        raise CoordinationError("No complete review pointer exists in this output directory")
    with _build_lock(out):
        pointer = read_json(out / "latest.json")
        if not isinstance(pointer, dict):
            raise CoordinationError("Invalid latest review pointer")
        issue_id = pointer.get("issue_id", "")
        if not isinstance(issue_id, str) or not re.fullmatch(r"[0-9a-f]{64}", issue_id):
            raise CoordinationError("Invalid latest review pointer")
        issue = out / "issues" / issue_id
        if file_hash(issue / "manifest.json") != pointer.get("manifest_sha256"):
            raise CoordinationError("Review manifest changed after pointer publication")
        manifest = _verify_package(issue)
        current = resolve_project(project_path)
        rendering = manifest.get("rendering")
        if visuals is not None and bool(rendering) != visuals:
            raise CoordinationError("Review rendering mode differs from the requested mode")
        if rendering is not None:
            current_rendering = _visual_configuration(rendering["width_px"])
            if current_rendering != rendering:
                raise CoordinationError(
                    "Review is stale: visual renderer/font configuration changed"
                )
        if (
            current["input_hash"] != manifest["input_hash"]
            or _issue_identity(current["input_hash"], rendering) != issue_id
            or manifest.get("issue_id") != issue_id
        ):
            raise CoordinationError(
                "Review is stale: source, study, code, rule or publication dependency changed"
            )
        if manifest["model_hash"] != current["model_hash"]:
            raise CoordinationError("Review model fingerprint differs from current resolution")
        return {"path": str(issue), "manifest": manifest}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", type=Path, default=DEFAULT_PROJECT, help="repository-authored JSON study"
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUTPUT, help="isolated generated review directory"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="verify current inputs and all generated artifacts"
    )
    mode.add_argument(
        "--study-template",
        type=Path,
        help="write a new empty source study pinned to the current baseline",
    )
    mode.add_argument(
        "--release",
        action="store_true",
        help="build and select a complete current-baseline review release",
    )
    mode.add_argument(
        "--check-release",
        action="store_true",
        help="verify selected review release and current source freshness",
    )
    mode.add_argument(
        "--rollback",
        metavar="RELEASE_ID",
        help="select a verified retained review release without claiming freshness",
    )
    mode.add_argument(
        "--watch",
        action="store_true",
        help="rebuild isolated candidates after debounced source edits; Ctrl-C to stop",
    )
    mode.add_argument(
        "--migrate-study",
        type=Path,
        metavar="NEW_STUDY",
        help="rebase --project into a new candidate only when every original field precondition matches",
    )
    parser.add_argument(
        "--migration-report",
        type=Path,
        help="exclusive migration report output; defaults to NEW_STUDY.migration.json",
    )
    parser.add_argument("--scenario-id", default="UNADOPTED_STUDY")
    parser.add_argument(
        "--visuals",
        action="store_true",
        help="include pinned-font PNG previews and a contact sheet",
    )
    parser.add_argument(
        "--require-no-fail",
        action="store_true",
        help="exit 2 for geometric FAIL findings; OPEN is still unresolved",
    )
    args = parser.parse_args(argv)
    if args.migration_report and not args.migrate_study:
        parser.error("--migration-report requires --migrate-study")
    if args.watch and args.require_no_fail:
        parser.error("--require-no-fail is a one-shot exit status; use --watch without it")
    try:
        if args.migrate_study:
            from dreamhouse.coordination.migration import prepare_migration, write_migration

            original_hash = file_hash(args.project)
            document = read_json(args.project)
            snapshot = resolve_project(DEFAULT_PROJECT)
            plan = prepare_migration(document, snapshot)
            if (
                file_hash(args.project) != original_hash
                or dependency_hashes(DEFAULT_PROJECT) != snapshot["build_dependencies"]
            ):
                raise CoordinationError("Migration inputs changed; retry from stable sources")
            args.migrate_study.parent.mkdir(parents=True, exist_ok=True)
            if args.migration_report:
                args.migration_report.parent.mkdir(parents=True, exist_ok=True)
            written = write_migration(plan, args.migrate_study, args.migration_report)
            print(f"Migration report: {written['report']}")
            if "study" not in written:
                print("Migration blocked: original expected values differ; no study was created.")
                return 2
            print(f"Migrated candidate: {written['study']}")
            print(
                "Full reevaluation is required; unchanged context equivalence and adoption are not asserted."
            )
            return 0
        if args.watch:
            from dreamhouse.coordination.watch import build_fresh_process, watch_sources

            watch_sources(
                args.project,
                lambda: build_fresh_process(args.project, args.out, visuals=args.visuals),
            )
            return 0
        if args.rollback or args.check_release:
            from dreamhouse.coordination.publication import read_current_release, rollback_release

            release_root = _output_directory(args.out) / "published"
            result = (
                rollback_release(args.rollback, release_root=release_root)
                if args.rollback
                else read_current_release(
                    release_root, require_fresh=True, project_path=args.project
                )
            )
            print(
                f"{'Selected retained' if args.rollback else 'Verified'} release: {result['index_path']}"
            )
            print(
                f"Release ID: {result['release_id']}; source freshness: {'not revalidated' if args.rollback else 'verified now'}; construction authority: false"
            )
            return 0
        if args.study_template:
            snapshot = resolve_project(args.project)
            template = study_template(snapshot, args.scenario_id)
            args.study_template.parent.mkdir(parents=True, exist_ok=True)
            with args.study_template.open("x", encoding="utf-8") as stream:
                stream.write(json_text(template))
            print(f"Study template: {args.study_template}")
            return 0
        result = (
            check_candidate(args.project, args.out, visuals=True if args.visuals else None)
            if args.check
            else build_candidate(args.project, args.out, visuals=args.visuals)
        )
        print(f"{'Verified' if args.check else 'Built'} review: {result['path']}/index.html")
        print(
            f"Check status: {result['manifest']['check_status']}; engineering and construction authority: false"
        )
        if args.release:
            from dreamhouse.coordination.publication import publish_candidate

            release = publish_candidate(
                args.project,
                candidate_out=args.out,
                release_root=_output_directory(args.out) / "published",
            )
            print(f"Released review: {release['index_path']}")
            print(f"Release ID: {release['release_id']}; construction authority: false")
        return 2 if args.require_no_fail and result["manifest"]["check_status"] == "FAIL" else 0
    except KeyboardInterrupt:
        print("Source watch stopped; previous complete review retained.")
        return 0
    except (CoordinationError, ValueError, KeyError, TypeError, OSError, RuntimeError) as error:
        print(f"Coordination failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
