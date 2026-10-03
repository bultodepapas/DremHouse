"""Publish verified coordination reviews as immutable, purpose-specific releases.

The release tree is separate from the current drawing catalog. A single atomic
``current.json`` pointer selects one complete immutable release; prior releases remain
available for inspection and rollback. A release is coordination evidence, never design
adoption, engineering approval, or construction authority.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from dreamhouse.coordination.model import (
    DEFAULT_PROJECT,
    ROOT,
    CoordinationError,
    digest,
    file_hash,
    json_text,
    read_json,
    resolve_project,
)

DEFAULT_OUTPUT = ROOT / ".build/coordination"
DEFAULT_PUBLICATION_ROOT = DEFAULT_OUTPUT / "published"
RELEASES_DIRECTORY = "releases"
POINTER_FILE = "current.json"
INDEX_FILE = "index.html"
RELEASE_MANIFEST = "release.json"
CANDIDATE_MANIFEST = "source_candidate_manifest.json"
PUBLICATION_SCHEMA_VERSION = 1
RELEASE_ID_PATTERN = re.compile(r"^[0-9a-f]{64}$")
FRESHNESS_POLICY = "verified against source dependencies at publication time only"

LIMITATIONS = [
    "OPEN coordination findings remain open; release does not approve them.",
    "This review is not design adoption, engineering approval, procurement approval, or construction authority.",
    "A study with requested model changes remains a candidate and cannot be released as the current baseline.",
    "Source freshness is checked at publication time only; immutable releases are historical snapshots afterward.",
    "The current published drawing aliases and planos/actual/catalog.json are not modified.",
    "Rollback selects an existing complete release and does not rebuild or assert source freshness.",
]


def _publication_root(value: Path | str) -> Path:
    raw = Path(value).expanduser()
    if raw.is_symlink():
        raise CoordinationError("Publication root cannot be a symlink")
    root = raw.resolve()
    if root == ROOT or (root.is_relative_to(ROOT) and not root.is_relative_to(ROOT / ".build")):
        raise CoordinationError("Choose a publication root under .build/ or outside the repository")
    return root


def _candidate_output(value: Path | str, publication_root: Path) -> Path:
    out = Path(value).expanduser().resolve()
    if out == publication_root or out.is_relative_to(publication_root):
        raise CoordinationError("Publication output cannot contain or replace its candidate source")
    # The intended default is a sibling child, <candidate-out>/published.
    if publication_root.is_relative_to(out) and publication_root.parent != out:
        raise CoordinationError("Publication root cannot be an ancestor of the candidate output")
    return out


def _safe_relative(name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise CoordinationError(f"Unsafe release artifact path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise CoordinationError(f"Unsafe release artifact path: {name!r}")
    if path.as_posix() != name:
        raise CoordinationError(f"Release artifact path is not normalized: {name!r}")
    if name in {RELEASE_MANIFEST, CANDIDATE_MANIFEST}:
        raise CoordinationError(f"Reserved release artifact path: {name}")
    return Path(*path.parts)


def _reject_symlink_components(root: Path, relative: Path) -> Path:
    path = root
    for index, component in enumerate(relative.parts):
        path = path / component
        if path.is_symlink():
            raise CoordinationError(f"Symlink path components are not allowed: {path}")
        if index < len(relative.parts) - 1 and path.exists() and not path.is_dir():
            raise CoordinationError(f"Artifact parent is not a directory: {path}")
    return path


def _releases_directory(root: Path, *, create: bool = False) -> Path:
    path = _reject_symlink_components(root, Path(RELEASES_DIRECTORY))
    if path.exists() and not path.is_dir():
        raise CoordinationError("Release inventory path is not a directory")
    if create:
        path.mkdir(exist_ok=True)
    return path


@contextmanager
def _publication_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".publication.lock"
    if lock_path.is_symlink():
        raise CoordinationError("Publication lock cannot be a symlink")
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _release_id(candidate_issue_id: str, candidate_manifest_sha256: str) -> str:
    return digest(
        {
            "purpose": "coordination review release",
            "publication_schema_version": PUBLICATION_SCHEMA_VERSION,
            "candidate_issue_id": candidate_issue_id,
            "candidate_manifest_sha256": candidate_manifest_sha256,
        }
    )


def _visual_configuration(width_px: int) -> dict:
    from dreamhouse.coordination.pipeline import _visual_configuration as pipeline_configuration

    return pipeline_configuration(width_px)


def _check_candidate(project_path: Path, candidate_out: Path) -> tuple[Path, dict, bytes]:
    # Lazy import avoids a cycle: pipeline already imports model, render, and rules.
    from dreamhouse.coordination.pipeline import check_candidate

    checked = check_candidate(project_path, candidate_out)
    issue = Path(checked["path"]).resolve()
    manifest_path = issue / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise CoordinationError("Verified candidate manifest is missing or substituted")
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_json(manifest_path)
    if manifest != checked["manifest"]:
        raise CoordinationError("Candidate manifest changed during publication verification")
    return issue, manifest, manifest_bytes


def _read_candidate_model(issue: Path, manifest: dict) -> tuple[dict, dict]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise CoordinationError("Candidate has no complete artifact inventory")
    if manifest.get("build_status") != "complete":
        raise CoordinationError("Only a complete coordination review can be released")
    if manifest.get("purpose") != "coordination review":
        raise CoordinationError("Only coordination review candidates can be released")
    if manifest.get("check_status") == "FAIL":
        raise CoordinationError("Candidate contains FAIL findings and cannot be released")
    if manifest.get("check_status") not in {"OPEN", "PASS"}:
        raise CoordinationError("Candidate has an unknown review status")
    if manifest.get("engineering_approval") is not False:
        raise CoordinationError("Candidate must retain engineering_approval=false")
    if manifest.get("construction_authority") is not False:
        raise CoordinationError("Candidate must retain construction_authority=false")
    if manifest.get("published_aliases_promoted") is not False:
        raise CoordinationError("Candidate must not promote published drawing aliases")

    for required in ("model.json", "changes.json", INDEX_FILE):
        if required not in artifacts:
            raise CoordinationError(f"Candidate release is missing required artifact: {required}")
    model = read_json(issue / "model.json")
    changes = read_json(issue / "changes.json")
    if model.get("model_hash") != manifest.get("model_hash"):
        raise CoordinationError("Candidate manifest and resolved model fingerprints differ")
    if model.get("changes_requested") != {}:
        raise CoordinationError("Studies with requested model changes remain candidates")
    if model.get("model_hash") != model.get("base_model_hash"):
        raise CoordinationError("Only the current baseline model can be released")
    if any(changes.get(field) for field in ("added", "removed", "modified", "context_changes")):
        raise CoordinationError("Candidate contains model or context changes from its baseline")
    dependencies = model.get("build_dependencies")
    if not isinstance(dependencies, dict) or not dependencies:
        raise CoordinationError("Candidate does not record source dependency hashes")
    return model, changes


def _bootstrap_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dream House · published coordination review</title>
<style>
body { margin: 2rem auto; max-width: 48rem; padding: 0 1rem; color: #172A32;
  background: #F4F0E7; font: 16px/1.5 system-ui, sans-serif; }
main { background: #FFFDFA; border: 1px solid #B9C0BD; border-radius: 5px; padding: 1.5rem; }
.warning { color: #8A5A16; font-weight: 700; }
</style>
</head>
<body><main>
<h1>Published coordination review</h1>
<p id="status">Reading the atomic current release pointer…</p>
<p><a id="open-release" hidden>Open the immutable review package</a></p>
<noscript>Enable JavaScript or open the immutable review path returned by the publish command.</noscript>
<script>
(() => {
  const status = document.getElementById('status');
  const link = document.getElementById('open-release');
  fetch('./current.json', {cache: 'no-store'})
    .then((response) => {
      if (!response.ok) throw new Error('No current release pointer is available.');
      return response.json();
    })
    .then((pointer) => {
      if (!/^[0-9a-f]{64}$/.test(pointer.release_id || '')) {
        throw new Error('The current release pointer is invalid.');
      }
      const target = `releases/${pointer.release_id}/index.html`;
      link.href = target;
      link.hidden = false;
      link.textContent = 'Open the immutable review package';
      if (pointer.source_freshness === 'not_revalidated') {
        status.className = 'warning';
        status.textContent = 'A historical release was selected by rollback. Source freshness was not revalidated.';
        return;
      }
      status.textContent = 'Opening the immutable review. Source freshness was checked at publication only.';
      window.location.replace(target);
    })
    .catch((error) => {
      status.className = 'warning';
      status.textContent = `${error.message} For file:// access, use the immutable release path printed by the publish command.`;
    });
})();
</script>
</main></body>
</html>
"""


def _atomic_write(path: Path, contents: bytes) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def _ensure_bootstrap(root: Path) -> None:
    path = root / INDEX_FILE
    expected = _bootstrap_html().encode("utf-8")
    if path.is_symlink():
        raise CoordinationError("Publication index cannot be a symlink")
    if path.exists():
        if not path.is_file() or path.read_bytes() != expected:
            raise CoordinationError("Publication bootstrap was modified or substituted")
        return
    _atomic_write(path, expected)


def _copy_candidate(
    issue: Path, manifest: dict, manifest_bytes: bytes, stage: Path
) -> dict[str, str]:
    artifacts = manifest["artifacts"]
    copied: dict[str, str] = {}
    for name, expected_hash in sorted(artifacts.items()):
        relative = _safe_relative(name)
        source = _reject_symlink_components(issue, relative)
        if not source.is_file():
            raise CoordinationError(f"Candidate artifact is missing or substituted: {name}")
        if not source.resolve().is_relative_to(issue):
            raise CoordinationError(f"Candidate artifact escapes its issue package: {name}")
        contents = source.read_bytes()
        if _sha256(contents) != expected_hash:
            raise CoordinationError(f"Candidate artifact changed during release copy: {name}")
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
        copied[name] = _sha256(contents)

    (stage / CANDIDATE_MANIFEST).write_bytes(manifest_bytes)
    return copied


def _tree_files(root: Path) -> set[str]:
    actual = set()
    for directory, subdirectories, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        for child in subdirectories:
            path = current / child
            if path.is_symlink():
                raise CoordinationError(f"Symlink directories are not allowed in releases: {path}")
        for filename in filenames:
            path = current / filename
            if path.is_symlink():
                raise CoordinationError(f"Symlink files are not allowed in releases: {path}")
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
    return actual


def _verify_release_path(
    release_path: Path,
    release_id: str,
    *,
    expected_manifest_sha256: str | None = None,
) -> dict:
    if release_path.is_symlink() or not release_path.is_dir():
        raise CoordinationError(f"Release package is missing or substituted: {release_id}")
    metadata_path = release_path / RELEASE_MANIFEST
    candidate_manifest_path = release_path / CANDIDATE_MANIFEST
    if metadata_path.is_symlink() or candidate_manifest_path.is_symlink():
        raise CoordinationError("Release provenance files cannot be symlinks")
    if not metadata_path.is_file() or not candidate_manifest_path.is_file():
        raise CoordinationError("Release provenance is incomplete")
    actual_manifest_hash = file_hash(metadata_path)
    if expected_manifest_sha256 is not None and actual_manifest_hash != expected_manifest_sha256:
        raise CoordinationError("Release manifest changed after publication")
    release = read_json(metadata_path)
    if release.get("schema_version") != PUBLICATION_SCHEMA_VERSION:
        raise CoordinationError("Unsupported publication release schema")
    if release.get("release_id") != release_id:
        raise CoordinationError("Release identity differs from its directory")
    if (
        release.get("build_status") != "complete"
        or release.get("purpose") != "coordination review release"
    ):
        raise CoordinationError("Release package is not complete coordination review evidence")
    if (
        release.get("engineering_approval") is not False
        or release.get("construction_authority") is not False
        or release.get("published_aliases_promoted") is not False
    ):
        raise CoordinationError("Release cannot grant authority or promote drawing aliases")
    if release.get("candidate_check_status") == "FAIL":
        raise CoordinationError("A FAIL candidate cannot be a complete release")

    candidate_manifest_bytes = candidate_manifest_path.read_bytes()
    if _sha256(candidate_manifest_bytes) != release.get("source_candidate_manifest_sha256"):
        raise CoordinationError("Source candidate manifest changed in the release")
    candidate_manifest = read_json(candidate_manifest_path)
    artifacts = release.get("artifacts")
    if not isinstance(artifacts, dict) or candidate_manifest.get("artifacts") != artifacts:
        raise CoordinationError("Release output inventory differs from its source candidate")
    if not {"index.html", "model.json", "changes.json"}.issubset(artifacts):
        raise CoordinationError("Release omits required review, model, or change artifacts")
    if (
        candidate_manifest.get("build_status") != "complete"
        or candidate_manifest.get("purpose") != "coordination review"
        or candidate_manifest.get("check_status") not in {"OPEN", "PASS"}
        or candidate_manifest.get("engineering_approval") is not False
        or candidate_manifest.get("construction_authority") is not False
        or candidate_manifest.get("published_aliases_promoted") is not False
        or candidate_manifest.get("check_status") != release.get("candidate_check_status")
    ):
        raise CoordinationError("Source candidate manifest violates release-purpose limits")
    if (
        _release_id(
            candidate_manifest.get("issue_id", ""),
            release.get("source_candidate_manifest_sha256", ""),
        )
        != release_id
    ):
        raise CoordinationError("Release ID does not match its source candidate provenance")
    expected_files = set(artifacts) | {RELEASE_MANIFEST, CANDIDATE_MANIFEST}
    if _tree_files(release_path) != expected_files:
        raise CoordinationError("Release file inventory differs from its manifest")
    for name, expected_hash in artifacts.items():
        relative = _safe_relative(name)
        artifact = _reject_symlink_components(release_path, relative)
        if not artifact.is_file() or file_hash(artifact) != expected_hash:
            raise CoordinationError(f"Changed or missing release artifact: {name}")
    if (
        candidate_manifest.get("issue_id") != release.get("source_candidate_issue_id")
        or candidate_manifest.get("input_hash") != release.get("source_input_hash")
        or candidate_manifest.get("model_hash") != release.get("source_model_hash")
        or candidate_manifest.get("rendering") != release.get("source_rendering")
        or candidate_manifest.get("hash_policy") != release.get("source_hash_policy")
    ):
        raise CoordinationError("Release metadata differs from source candidate provenance")
    model = read_json(release_path / "model.json")
    changes = read_json(release_path / "changes.json")
    if (
        model.get("model_hash") != release.get("source_model_hash")
        or model.get("base_model_hash") != model.get("model_hash")
        or model.get("changes_requested") != {}
        or model.get("build_dependencies") != release.get("source_dependency_hashes")
        or model.get("project_path") != release.get("source_project_path")
        or any(changes.get(field) for field in ("added", "removed", "modified", "context_changes"))
    ):
        raise CoordinationError("Release no longer verifies as a no-change current baseline")
    expected_release = {
        "schema_version": PUBLICATION_SCHEMA_VERSION,
        "build_status": "complete",
        "purpose": "coordination review release",
        "release_id": release_id,
        "source_candidate_issue_id": candidate_manifest["issue_id"],
        "source_candidate_manifest_sha256": _sha256(candidate_manifest_bytes),
        "source_input_hash": candidate_manifest["input_hash"],
        "source_model_hash": candidate_manifest["model_hash"],
        "source_rendering": candidate_manifest.get("rendering"),
        "source_hash_policy": candidate_manifest["hash_policy"],
        "source_dependency_hashes": model["build_dependencies"],
        "source_project_path": model.get("project_path"),
        "candidate_check_status": candidate_manifest["check_status"],
        "engineering_approval": False,
        "construction_authority": False,
        "published_aliases_promoted": False,
        "freshness_policy": FRESHNESS_POLICY,
        "limitations": list(LIMITATIONS),
        "artifacts": artifacts,
    }
    if release != expected_release:
        raise CoordinationError("Release metadata differs from verified candidate provenance")
    return release


def _current_pointer(
    release_id: str,
    release: dict,
    release_manifest_sha256: str,
    *,
    selection_reason: str,
    source_freshness: str,
    rollback_from_release_id: str | None = None,
) -> dict:
    pointer = {
        "schema_version": 1,
        "release_id": release_id,
        "release_manifest_sha256": release_manifest_sha256,
        "review_index": f"{RELEASES_DIRECTORY}/{release_id}/{INDEX_FILE}",
        "source_candidate_issue_id": release["source_candidate_issue_id"],
        "source_input_hash": release["source_input_hash"],
        "source_model_hash": release["source_model_hash"],
        "selection_reason": selection_reason,
        "source_freshness": source_freshness,
    }
    if rollback_from_release_id is not None:
        pointer["rollback_from_release_id"] = rollback_from_release_id
    return pointer


def _write_current_pointer(root: Path, pointer: dict) -> None:
    _atomic_write(root / POINTER_FILE, json_text(pointer).encode("utf-8"))


def publish_candidate(
    project_path: Path = DEFAULT_PROJECT,
    candidate_out: Path = DEFAULT_OUTPUT,
    release_root: Path = DEFAULT_PUBLICATION_ROOT,
) -> dict:
    """Copy a verified current-baseline candidate into a complete immutable release.

    OPEN findings remain reviewable. FAIL findings and requested source-study changes are
    refused. The function never writes the current drawing catalog or its aliases.
    """

    project_path = Path(project_path).expanduser().resolve()
    root = _publication_root(release_root)
    candidate_directory = _candidate_output(candidate_out, root)
    issue, manifest, manifest_bytes = _check_candidate(project_path, candidate_directory)
    model, _changes = _read_candidate_model(issue, manifest)
    candidate_manifest_sha256 = _sha256(manifest_bytes)
    release_id = _release_id(manifest["issue_id"], candidate_manifest_sha256)
    releases = _releases_directory(root)
    target = releases / release_id

    with _publication_lock(root):
        releases = _releases_directory(root, create=True)
        _ensure_bootstrap(root)
        if target.exists():
            release = _verify_release_path(target, release_id)
        else:
            stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=releases))
            try:
                copied = _copy_candidate(issue, manifest, manifest_bytes, stage)
                if copied != manifest["artifacts"]:
                    raise CoordinationError("Copied release inventory differs from the candidate")
                release = {
                    "schema_version": PUBLICATION_SCHEMA_VERSION,
                    "build_status": "complete",
                    "purpose": "coordination review release",
                    "release_id": release_id,
                    "source_candidate_issue_id": manifest["issue_id"],
                    "source_candidate_manifest_sha256": candidate_manifest_sha256,
                    "source_input_hash": manifest["input_hash"],
                    "source_model_hash": manifest["model_hash"],
                    "source_rendering": manifest.get("rendering"),
                    "source_hash_policy": manifest["hash_policy"],
                    "source_dependency_hashes": model["build_dependencies"],
                    "source_project_path": model.get("project_path"),
                    "candidate_check_status": manifest["check_status"],
                    "engineering_approval": False,
                    "construction_authority": False,
                    "published_aliases_promoted": False,
                    "freshness_policy": FRESHNESS_POLICY,
                    "limitations": list(LIMITATIONS),
                    "artifacts": copied,
                }
                (stage / RELEASE_MANIFEST).write_text(json_text(release), encoding="utf-8")
                _verify_release_path(stage, release_id)
                os.replace(stage, target)
            finally:
                if stage.exists():
                    shutil.rmtree(stage)

        if (
            release.get("source_candidate_issue_id") != manifest["issue_id"]
            or release.get("source_candidate_manifest_sha256") != candidate_manifest_sha256
        ):
            raise CoordinationError("Existing release identity conflicts with this candidate")

        # Revalidate after copying so edits during a potentially large export leave the
        # previous current pointer untouched. A complete unselected release may remain
        # available if this late freshness check fails.
        current_issue, current_manifest, current_bytes = _check_candidate(
            project_path, candidate_directory
        )
        if (
            current_issue != issue
            or current_manifest != manifest
            or _sha256(current_bytes) != candidate_manifest_sha256
        ):
            raise CoordinationError("Candidate changed before the release pointer was updated")

        release = _verify_release_path(target, release_id)
        release_hash = file_hash(target / RELEASE_MANIFEST)
        pointer = _current_pointer(
            release_id,
            release,
            release_hash,
            selection_reason="publish",
            source_freshness="verified_at_publication",
        )
        _write_current_pointer(root, pointer)
    return {
        "release_id": release_id,
        "path": str(target),
        "index_path": str(target / INDEX_FILE),
        "bootstrap_path": str(root / INDEX_FILE),
        "pointer": pointer,
        "release": release,
    }


def verify_release(
    release_id: str,
    release_root: Path = DEFAULT_PUBLICATION_ROOT,
) -> dict:
    """Verify the immutable release manifest, full artifact inventory, and provenance."""

    if not RELEASE_ID_PATTERN.fullmatch(release_id):
        raise CoordinationError("Invalid release ID")
    root = _publication_root(release_root)
    release_path = _reject_symlink_components(root, Path(RELEASES_DIRECTORY) / release_id)
    release = _verify_release_path(release_path, release_id)
    return {
        "release_id": release_id,
        "path": str(release_path),
        "index_path": str(release_path / INDEX_FILE),
        "release_manifest_sha256": file_hash(release_path / RELEASE_MANIFEST),
        "release": release,
    }


def rollback_release(
    release_id: str,
    release_root: Path = DEFAULT_PUBLICATION_ROOT,
) -> dict:
    """Select a previously published complete release without rebuilding or refreshing it."""

    if not RELEASE_ID_PATTERN.fullmatch(release_id):
        raise CoordinationError("Invalid release ID")
    root = _publication_root(release_root)
    with _publication_lock(root):
        releases = _releases_directory(root)
        release_path = releases / release_id
        release = _verify_release_path(release_path, release_id)
        previous_pointer = root / POINTER_FILE
        previous_id = None
        if previous_pointer.is_file() and not previous_pointer.is_symlink():
            try:
                previous = read_json(previous_pointer)
            except (ValueError, OSError):
                previous = {}
            if not isinstance(previous, dict):
                previous = {}
            previous_id = previous.get("release_id")
            if not isinstance(previous_id, str) or not RELEASE_ID_PATTERN.fullmatch(previous_id):
                previous_id = None
        elif previous_pointer.exists() and not previous_pointer.is_symlink():
            raise CoordinationError("Current release pointer path is not a file")
        _ensure_bootstrap(root)
        pointer = _current_pointer(
            release_id,
            release,
            file_hash(release_path / RELEASE_MANIFEST),
            selection_reason="rollback",
            source_freshness="not_revalidated",
            rollback_from_release_id=previous_id,
        )
        _write_current_pointer(root, pointer)
    return {
        "release_id": release_id,
        "path": str(release_path),
        "index_path": str(release_path / INDEX_FILE),
        "bootstrap_path": str(root / INDEX_FILE),
        "pointer": pointer,
        "release": release,
    }


def read_current_release(
    release_root: Path = DEFAULT_PUBLICATION_ROOT,
    *,
    require_fresh: bool = False,
    project_path: Path = DEFAULT_PROJECT,
) -> dict:
    """Read and verify the selected release, optionally checking current source freshness.

    Freshness is compared directly against the current resolved source tree. It does not
    require the original candidate package to remain available. A rollback retains its
    ``not_revalidated`` selection marker unless this explicit check succeeds.
    """

    root = _publication_root(release_root)
    pointer_path = root / POINTER_FILE
    if pointer_path.is_symlink() or not pointer_path.is_file():
        raise CoordinationError("No valid current release pointer exists")
    try:
        pointer = read_json(pointer_path)
    except (ValueError, OSError) as exc:
        raise CoordinationError(f"Cannot read current release pointer: {exc}") from exc
    if not isinstance(pointer, dict):
        raise CoordinationError("Invalid current release pointer; expected an object")
    release_id = pointer.get("release_id")
    if not isinstance(release_id, str) or not RELEASE_ID_PATTERN.fullmatch(release_id):
        raise CoordinationError("Invalid current release ID")
    expected_index = f"{RELEASES_DIRECTORY}/{release_id}/{INDEX_FILE}"
    if pointer.get("review_index") != expected_index:
        raise CoordinationError("Current pointer does not target its immutable release index")
    if pointer.get("selection_reason") not in {"publish", "rollback"}:
        raise CoordinationError("Unknown current release selection reason")
    expected_freshness = (
        {"verified_at_publication"}
        if pointer["selection_reason"] == "publish"
        else {"not_revalidated"}
    )
    if pointer.get("source_freshness") not in expected_freshness:
        raise CoordinationError("Current pointer has an invalid source freshness state")

    result = verify_release(release_id, root)
    release = result["release"]
    if file_hash(Path(result["path"]) / RELEASE_MANIFEST) != pointer.get("release_manifest_sha256"):
        raise CoordinationError("Current pointer and immutable release manifest differ")
    for key in ("source_candidate_issue_id", "source_input_hash", "source_model_hash"):
        if pointer.get(key) != release.get(key):
            raise CoordinationError(f"Current pointer and release disagree on {key}")

    freshness_check = None
    if require_fresh:
        current = resolve_project(Path(project_path).expanduser().resolve())
        if (
            current["input_hash"] != release["source_input_hash"]
            or current["model_hash"] != release["source_model_hash"]
            or current["build_dependencies"] != release["source_dependency_hashes"]
            or current["changes_requested"] != {}
            or current["model_hash"] != current["base_model_hash"]
        ):
            raise CoordinationError(
                "Current release is stale or no longer matches a no-change baseline"
            )
        rendering = release.get("source_rendering")
        if rendering is not None and _visual_configuration(rendering["width_px"]) != rendering:
            raise CoordinationError("Current release visual renderer/font configuration is stale")
        freshness_check = {
            "status": "verified_now",
            "input_hash": current["input_hash"],
            "model_hash": current["model_hash"],
        }

    return {
        **result,
        "bootstrap_path": str(root / INDEX_FILE),
        "pointer": pointer,
        "source_freshness": pointer["source_freshness"],
        "freshness_check": freshness_check,
    }
