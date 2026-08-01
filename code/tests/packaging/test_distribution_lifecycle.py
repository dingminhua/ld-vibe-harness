from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPERATIONS = (
    "read-specification-candidates",
    "read-specification-content",
    "read-specification-context",
    "resolve-governance-scope",
    "precheck-git-commit",
    "find-fact-object-candidates",
    "check-fact-integrity",
    "read-fact-objects",
    "prepare-fact-object-draft",
    "create-fact-object",
    "prepare-file-asset-intake",
    "create-file-asset",
    "delete-file-asset",
    "update-fact-object",
    "update-workcase",
    "close-workcase",
    "correct-closed-workcase",
    "read-action-template-candidates",
    "read-action-template-content",
)


@dataclass(frozen=True, slots=True)
class ReleaseArtifacts:
    current_version: str
    old_version: str
    current_wheel: Path
    old_wheel: Path
    sdist_wheel: Path
    current_snapshot_sha256: str
    old_snapshot_sha256: str


@dataclass(frozen=True, slots=True)
class InstalledEnvironment:
    root: Path
    python: Path
    helper: Path
    doctor: Path
    context_recovery_runner: Path
    commit_msg_runner: Path
    git_hook_manager: Path
    purelib: Path
    runtime_dependencies: Path

    @property
    def process_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(self.runtime_dependencies)
        return environment


def _run_checked(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(arguments, cwd=cwd, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, (arguments, completed.stdout, completed.stderr)
    return completed


def _copy_release_source(destination: Path) -> None:
    destination.mkdir()
    for name in ("README.md", "pyproject.toml", "setup.py"):
        shutil.copy2(PROJECT_ROOT / name, destination / name)
    shutil.copytree(PROJECT_ROOT / "code" / "ldvh", destination / "code" / "ldvh")
    shutil.copytree(PROJECT_ROOT / "specs", destination / "specs")
    shutil.copytree(PROJECT_ROOT / "skill", destination / "skill")
    shutil.copytree(PROJECT_ROOT / "icons", destination / "icons")
    _run_checked(["git", "init", "-q", str(destination)], cwd=destination.parent)


def _set_project_version(source: Path, old: str, new: str) -> None:
    project = source / "pyproject.toml"
    text = project.read_text(encoding="utf-8")
    needle = f'version = "{old}"'
    assert text.count(needle) == 1
    project.write_text(text.replace(needle, f'version = "{new}"'), encoding="utf-8")


def _only_artifact(directory: Path, pattern: str) -> Path:
    artifacts = tuple(directory.glob(pattern))
    assert len(artifacts) == 1, artifacts
    return artifacts[0]


def _build(source: Path, output: Path, kind: str) -> Path:
    output.mkdir()
    _run_checked(
        [sys.executable, "-m", "build", "--no-isolation", f"--{kind}", "--outdir", str(output), str(source)],
        cwd=source.parent,
    )
    return _only_artifact(output, "*.whl" if kind == "wheel" else "*.tar.gz")


def _snapshot_manifest(wheel: Path) -> dict[str, Any]:
    with zipfile.ZipFile(wheel) as archive:
        payload = archive.read("ldvh/_rule_snapshot/manifest.json")
    manifest = json.loads(payload)
    assert isinstance(manifest, dict)
    return manifest


@pytest.fixture(scope="module")
def release_artifacts(tmp_path_factory: pytest.TempPathFactory) -> ReleaseArtifacts:
    root = tmp_path_factory.mktemp("distribution-build")
    current_source = root / "current-source"
    old_source = root / "old-source"
    _copy_release_source(current_source)
    _copy_release_source(old_source)

    project = tomllib.loads((current_source / "pyproject.toml").read_text(encoding="utf-8"))
    current_version = project["project"]["version"]
    old_version = "0.0.0"
    assert current_version != old_version
    _set_project_version(old_source, current_version, old_version)
    (old_source / "code" / "ldvh" / "legacy_release_marker.py").write_text(
        '"""An old-RECORD-only member used by the distribution replacement test."""\n',
        encoding="utf-8",
    )

    current_wheel = _build(current_source, root / "current-wheel", "wheel")
    old_wheel = _build(old_source, root / "old-wheel", "wheel")
    sdist = _build(current_source, root / "current-sdist", "sdist")
    extracted = root / "sdist-extracted"
    extracted.mkdir()
    with tarfile.open(sdist, "r:gz") as archive:
        archive.extractall(extracted, filter="data")
    extracted_source = _only_artifact(extracted, "*")
    assert not (extracted_source / ".git").exists()
    sdist_wheel = _build(extracted_source, root / "sdist-wheel", "wheel")

    current_manifest = _snapshot_manifest(current_wheel)
    old_manifest = _snapshot_manifest(old_wheel)
    sdist_manifest = _snapshot_manifest(sdist_wheel)
    assert current_manifest == sdist_manifest
    assert current_manifest["version"] == current_version
    assert old_manifest["version"] == old_version
    assert current_manifest["snapshot_sha256"] != old_manifest["snapshot_sha256"]
    return ReleaseArtifacts(
        current_version=current_version,
        old_version=old_version,
        current_wheel=current_wheel,
        old_wheel=old_wheel,
        sdist_wheel=sdist_wheel,
        current_snapshot_sha256=current_manifest["snapshot_sha256"],
        old_snapshot_sha256=old_manifest["snapshot_sha256"],
    )


def test_release_artifacts_ship_integration_assets(release_artifacts: ReleaseArtifacts) -> None:
    expected_skill = (PROJECT_ROOT / "skill" / "SKILL.md").read_bytes()
    expected_icons = {path.name: path.read_bytes() for path in (PROJECT_ROOT / "icons").glob("*.png")}
    assert expected_icons, "icons/ must not be empty"
    for wheel in (release_artifacts.current_wheel, release_artifacts.sdist_wheel):
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
            assert "ldvh/_integration_assets/skill/SKILL.md" in names
            assert archive.read("ldvh/_integration_assets/skill/SKILL.md") == expected_skill
            for name, payload in expected_icons.items():
                member = f"ldvh/_integration_assets/icons/{name}"
                assert member in names
                assert archive.read(member) == payload


def _copy_runtime_dependencies(destination: Path) -> None:
    destination.mkdir()
    copied: set[Path] = set()
    for distribution_name in ("ruamel.yaml", "ruamel.yaml.clib"):
        distribution = importlib.metadata.distribution(distribution_name)
        for item in distribution.files or ():
            relative = Path(str(item))
            if not relative.parts:
                continue
            if relative.parts[0] != "ruamel" and not relative.name.startswith("_ruamel_yaml"):
                continue
            source = Path(distribution.locate_file(item))
            if not source.is_file() or relative in copied:
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.add(relative)
    assert (destination / "ruamel" / "yaml" / "__init__.py").is_file()


def _create_installed_environment(root: Path) -> InstalledEnvironment:
    subprocess.run([sys.executable, "-m", "venv", str(root)], check=True, capture_output=True)
    scripts = root / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    helper = scripts / ("ldvh.exe" if os.name == "nt" else "ldvh")
    doctor = scripts / ("ldvh-doctor.exe" if os.name == "nt" else "ldvh-doctor")
    context_recovery_runner = scripts / ("ldvh-context-recovery.exe" if os.name == "nt" else "ldvh-context-recovery")
    commit_msg_runner = scripts / ("ldvh-git-commit-msg.exe" if os.name == "nt" else "ldvh-git-commit-msg")
    git_hook_manager = scripts / ("ldvh-git-hook.exe" if os.name == "nt" else "ldvh-git-hook")
    purelib = Path(
        _run_checked(
            [str(python), "-c", 'import sysconfig; print(sysconfig.get_paths()["purelib"])'],
            cwd=root,
        ).stdout.strip()
    )
    dependencies = root / "runtime-dependencies"
    _copy_runtime_dependencies(dependencies)
    return InstalledEnvironment(
        root,
        python,
        helper,
        doctor,
        context_recovery_runner,
        commit_msg_runner,
        git_hook_manager,
        purelib,
        dependencies,
    )


def _pip(environment: InstalledEnvironment, *arguments: str) -> None:
    completed = subprocess.run(
        [str(environment.python), "-m", "pip", *arguments],
        cwd=environment.root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, (arguments, completed.stdout, completed.stderr)


def _cli(
    environment: InstalledEnvironment,
    cwd: Path,
    command: str,
    operation_key: str | None,
    payload: str,
    *,
    expected_exit: int = 0,
) -> dict[str, Any]:
    arguments = [str(environment.helper), command]
    if operation_key is not None:
        arguments.append(operation_key)
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        input=payload.encode("utf-8"),
        capture_output=True,
        env=environment.process_environment,
        check=False,
    )
    assert completed.returncode == expected_exit, (arguments, completed.stdout, completed.stderr)
    assert completed.stderr == b""
    decoded = completed.stdout.decode("utf-8")
    response = json.loads(decoded)
    assert decoded == json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n"
    return response


def _context_recovery(
    environment: InstalledEnvironment,
    cwd: Path,
    workspace: Path,
    work_object_locator: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            str(environment.context_recovery_runner),
            "--helper-executable",
            str(environment.helper),
            "--workspace-root",
            str(workspace),
            "--work-object-locator",
            str(work_object_locator),
            "--helper-cwd",
            str(cwd),
        ],
        cwd=cwd,
        input="",
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment.process_environment,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stderr == ""
    projection = json.loads(completed.stdout)
    assert isinstance(projection, dict)
    assert projection["contract"] == "ldvh-context-recovery/1"
    return projection


def _references(value: Any) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("kind") in {"rule", "implementation"} and isinstance(value.get("locator"), str):
            references.append(value)
        for child in value.values():
            references.extend(_references(child))
    elif isinstance(value, list):
        for child in value:
            references.extend(_references(child))
    return references


def _assert_installed_identity(response: dict[str, Any], version: str, snapshot_sha256: str) -> None:
    references = _references(response)
    assert references
    for reference in references:
        assert reference["version"] == version
        details = reference["details"]
        assert details["distribution"] == "ld-vibe-harness"
        assert "git_worktree_root" not in details
        if reference["kind"] == "rule":
            assert details["rule_source_view"] == "installed_release_snapshot"
            assert details["snapshot_sha256"] == snapshot_sha256
        else:
            assert details["implementation_source_view"] == "installed_distribution"
            assert "snapshot_sha256" not in details


def _payload(workspace: Path, project: Path, arguments: dict[str, Any]) -> str:
    return json.dumps(
        {
            "work_object_locators": [str(project)],
            "arguments": {"workspace_root": str(workspace), **arguments},
        }
    )


def _managed_project(root: Path) -> tuple[Path, Path]:
    workspace = root / "workspace"
    project = workspace / "project"
    project.mkdir(parents=True)
    for directory in ("workcases", "adrs", "pitfalls", "sparks", "studies"):
        (project / "ldvh-base" / directory).mkdir(parents=True, exist_ok=True)
    _run_checked(["git", "init", "-q", str(project)], cwd=root)
    (project / "observed.txt").write_text("governed project\n", encoding="utf-8")
    (workspace / "LDVH-GOVERNED-PROJECTS.yaml").write_text(
        "\n".join(
            [
                "product_name: Distribution Matrix",
                "product_description: Isolated installed-package verification.",
                "projects:",
                "  - id: sample",
                f"    path: {project}",
                "    name: Sample",
                "    description: Temporary governed project.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return workspace, project


def _valid_pair(
    environment: InstalledEnvironment,
    project: Path,
    operation_key: str,
    payload: str,
    version: str,
    snapshot_sha256: str,
) -> dict[str, Any]:
    checked = _cli(environment, project, "capabilities", operation_key, payload)
    called = _cli(environment, project, "call", operation_key, payload)
    assert checked["outcome"] == "ok"
    assert called["outcome"] in {"ok", "no_change"}
    _assert_installed_identity(checked, version, snapshot_sha256)
    _assert_installed_identity(called, version, snapshot_sha256)
    return called


def _invalid_pair(
    environment: InstalledEnvironment,
    project: Path,
    operation_key: str,
    payload: str,
) -> None:
    before = _project_state(project)
    for command in ("capabilities", "call"):
        response = _cli(environment, project, command, operation_key, payload, expected_exit=2)
        assert response["outcome"] == "invalid_request"
    assert _project_state(project) == before


def _project_files(project: Path) -> dict[str, str]:
    return {
        path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(project.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(project).parts
    }


def _git_observation(project: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(project), *arguments],
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, (arguments, completed.stdout, completed.stderr)
    return completed.stdout


def _project_state(project: Path) -> tuple[dict[str, str], bytes, bytes]:
    return (
        _project_files(project),
        _git_observation(project, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        _git_observation(project, "ls-files", "--stage", "-z"),
    )


def _assert_only_file_changed(before: dict[str, str], after: dict[str, str], expected: str) -> None:
    assert {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)} == {expected}


def _snapshot_tree_fingerprint(snapshot: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(snapshot.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(snapshot).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _exercise_operation_matrix(
    environment: InstalledEnvironment,
    root: Path,
    version: str,
    snapshot_sha256: str,
) -> None:
    workspace, project = _managed_project(root)
    snapshot = environment.purelib / "ldvh" / "_rule_snapshot"
    snapshot_before = _snapshot_tree_fingerprint(snapshot)

    governance = _payload(workspace, project, {})
    governance_response = _valid_pair(
        environment,
        project,
        "resolve-governance-scope",
        governance,
        version,
        snapshot_sha256,
    )
    assert governance_response["result"]["object_resolutions"][0]["git_worktree_root"] == str(project.resolve())
    _invalid_pair(
        environment,
        project,
        "resolve-governance-scope",
        json.dumps({"work_object_locators": [{"path": str(project)}]}),
    )

    _run_checked(["git", "-C", str(project), "add", "observed.txt"], cwd=root)
    commit_precheck = _payload(
        workspace,
        project,
        {"message": "test: 验证安装发行提交预检"},
    )
    precheck_response = _valid_pair(
        environment,
        project,
        "precheck-git-commit",
        commit_precheck,
        version,
        snapshot_sha256,
    )
    assert precheck_response["result"]["mechanical_outcome"] == "passed"
    assert precheck_response["result"]["candidate"]["paths"] == ["observed.txt"]
    _invalid_pair(
        environment,
        project,
        "precheck-git-commit",
        _payload(
            workspace,
            project,
            {"message": "test: 验证非法 Index 输入", "index_file": "/tmp/untrusted-index"},
        ),
    )

    _valid_pair(environment, project, "read-specification-candidates", "", version, snapshot_sha256)
    _invalid_pair(
        environment,
        project,
        "read-specification-candidates",
        json.dumps({"requested_disclosure": "L4"}),
    )
    specification_content = json.dumps(
        {
            "arguments": {"selections": [{"responsibility_key": "ldvh-root", "heading_path": None}]},
            "requested_disclosure": "L4",
        }
    )
    _valid_pair(
        environment,
        project,
        "read-specification-content",
        specification_content,
        version,
        snapshot_sha256,
    )
    _invalid_pair(
        environment,
        project,
        "read-specification-content",
        json.dumps({"arguments": {"selections": []}, "requested_disclosure": "L4"}),
    )
    specification_context = json.dumps(
        {
            "arguments": {"contexts": [{"responsibility_key": "ldvh-root", "primary_heading_paths": []}]},
            "requested_disclosure": "L3",
        }
    )
    _valid_pair(
        environment,
        project,
        "read-specification-context",
        specification_context,
        version,
        snapshot_sha256,
    )
    _invalid_pair(
        environment,
        project,
        "read-specification-context",
        json.dumps({"arguments": {"contexts": []}, "requested_disclosure": "L3"}),
    )

    _valid_pair(environment, project, "read-action-template-candidates", "", version, snapshot_sha256)
    _invalid_pair(
        environment,
        project,
        "read-action-template-candidates",
        json.dumps({"arguments": {"template_keys": [1]}}),
    )
    template_content = json.dumps({"arguments": {"template_keys": ["git-commit"]}})
    _valid_pair(
        environment,
        project,
        "read-action-template-content",
        template_content,
        version,
        snapshot_sha256,
    )
    _invalid_pair(
        environment,
        project,
        "read-action-template-content",
        json.dumps({"arguments": {"template_keys": []}}),
    )

    candidate_payload = _payload(
        workspace,
        project,
        {"governed_project_id": "sample", "card_layer": "F1"},
    )
    candidate_response = _valid_pair(
        environment,
        project,
        "find-fact-object-candidates",
        candidate_payload,
        version,
        snapshot_sha256,
    )
    assert candidate_response["result"]["recovery_manifest"]["git_worktree_root"] == str(project.resolve())
    _invalid_pair(
        environment,
        project,
        "find-fact-object-candidates",
        _payload(workspace, project, {"governed_project_id": "sample"}),
    )

    prepare_payload = _payload(
        workspace,
        project,
        {"governed_project_id": "sample", "fact_type_key": "spark"},
    )
    before_prepare = _project_state(project)
    checked_prepare = _cli(environment, project, "capabilities", "prepare-fact-object-draft", prepare_payload)
    assert checked_prepare["outcome"] == "ok"
    _assert_installed_identity(checked_prepare, version, snapshot_sha256)
    assert _project_state(project) == before_prepare
    prepared = _cli(environment, project, "call", "prepare-fact-object-draft", prepare_payload)
    assert prepared["outcome"] == "ok"
    _assert_installed_identity(prepared, version, snapshot_sha256)
    assert _project_state(project) == before_prepare
    _invalid_pair(
        environment,
        project,
        "prepare-fact-object-draft",
        _payload(workspace, project, {"governed_project_id": "sample", "fact_type_key": "unknown"}),
    )
    basis = prepared["result"]
    create_payload = _payload(
        workspace,
        project,
        {
            "draft_basis": {
                key: basis[key]
                for key in (
                    "governed_project_id",
                    "fact_type_key",
                    "candidate_object_id",
                    "schema_fingerprint",
                    "worktree_fingerprint",
                )
            },
            "fact_object": {
                "title": "Installed distribution lifecycle",
                "status": "open",
                "summary": "Created only in the isolated governed project.",
                "priority": "P2",
            },
        },
    )
    fact_path = project / "ldvh-base" / "sparks" / "spark-0001.yaml"
    before_create = _project_state(project)
    checked_create = _cli(environment, project, "capabilities", "create-fact-object", create_payload)
    assert checked_create["outcome"] == "ok"
    _assert_installed_identity(checked_create, version, snapshot_sha256)
    assert _project_state(project) == before_create
    created = _cli(environment, project, "call", "create-fact-object", create_payload)
    assert created["outcome"] == "ok"
    _assert_installed_identity(created, version, snapshot_sha256)
    assert fact_path.is_file()
    _assert_only_file_changed(before_create[0], _project_files(project), "ldvh-base/sparks/spark-0001.yaml")
    assert _git_observation(project, "ls-files", "--stage", "-z") == before_create[2]
    created_bytes = fact_path.read_bytes()
    _invalid_pair(
        environment,
        project,
        "create-fact-object",
        _payload(workspace, project, {"fact_object": {}}),
    )
    assert fact_path.read_bytes() == created_bytes
    assert tuple((project / "ldvh-base" / "sparks").glob("*.yaml")) == (fact_path,)

    fact_ref = {"governed_project_id": "sample", "fact_type_key": "spark", "object_id": "spark-0001"}
    read_payload = _payload(workspace, project, {"fact_refs": [fact_ref]})
    read = _valid_pair(
        environment,
        project,
        "read-fact-objects",
        read_payload,
        version,
        snapshot_sha256,
    )
    _invalid_pair(
        environment,
        project,
        "read-fact-objects",
        _payload(workspace, project, {"fact_refs": []}),
    )
    item = read["result"]["items"][0]
    target = dict(item["fact_object"])
    for key in ("object_id", "fact_type_key", "created_at", "updated_at"):
        target.pop(key)
    target["summary"] = "Updated only in the isolated governed project."
    update_payload = _payload(
        workspace,
        project,
        {
            "fact_ref": fact_ref,
            "expected_content_fingerprint": item["content_fingerprint"],
            "fact_object": target,
        },
    )
    before_update = fact_path.read_bytes()
    before_update_state = _project_state(project)
    checked_update = _cli(environment, project, "capabilities", "update-fact-object", update_payload)
    assert checked_update["outcome"] == "ok"
    _assert_installed_identity(checked_update, version, snapshot_sha256)
    assert _project_state(project) == before_update_state
    updated = _cli(environment, project, "call", "update-fact-object", update_payload)
    assert updated["outcome"] == "ok"
    _assert_installed_identity(updated, version, snapshot_sha256)
    assert fact_path.read_bytes() != before_update
    _assert_only_file_changed(before_update_state[0], _project_files(project), "ldvh-base/sparks/spark-0001.yaml")
    assert _git_observation(project, "ls-files", "--stage", "-z") == before_update_state[2]
    updated_bytes = fact_path.read_bytes()
    _invalid_pair(
        environment,
        project,
        "update-fact-object",
        _payload(
            workspace,
            project,
            {"fact_ref": fact_ref, "expected_content_fingerprint": "bad", "fact_object": target},
        ),
    )
    assert fact_path.read_bytes() == updated_bytes

    assert _snapshot_tree_fingerprint(snapshot) == snapshot_before
    assert not tuple(environment.purelib.rglob("spark-0001.yaml"))
    assert not tuple(environment.purelib.rglob("LDVH-GOVERNED-PROJECTS.yaml"))
    assert not tuple(environment.purelib.rglob(".git"))
    git_probe = subprocess.run(
        ["git", "-C", str(snapshot), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        check=False,
    )
    assert git_probe.returncode != 0


def _assert_version(
    environment: InstalledEnvironment,
    cwd: Path,
    version: str,
    snapshot_sha256: str,
) -> None:
    response = _cli(environment, cwd, "capabilities", None, "")
    assert response["outcome"] == "ok"
    assert len(response["result"]["operations"]) == len(OPERATIONS)
    _assert_installed_identity(response, version, snapshot_sha256)


def _assert_context_recovery_runner(environment: InstalledEnvironment, root: Path) -> None:
    workspace, project = _managed_project(root)
    decoy = root / "decoy-cwd"
    (decoy / "specs").mkdir(parents=True)
    (decoy / "specs" / "00-理念与构成.md").write_text("not the installed source\n", encoding="utf-8")

    assert environment.context_recovery_runner.is_file()
    projection = _context_recovery(environment, decoy, workspace, project)

    assert [operation["operation_key"] for operation in projection["operations"]] == [
        "resolve-governance-scope",
        "find-fact-object-candidates",
    ]
    governance_expand = next(
        item for item in projection["expand"] if item["operation_key"] == "resolve-governance-scope"
    )
    assert governance_expand["request"]["work_object_locators"] == [str(project)]
    assert not tuple(environment.purelib.rglob("codex_context.py"))


def _assert_doctor_runner(environment: InstalledEnvironment, root: Path) -> None:
    workspace, project = _managed_project(root)
    completed = subprocess.run(
        [
            str(environment.doctor),
            "--workspace-root",
            str(workspace),
            "--work-object-locator",
            str(project),
            "--helper-executable",
            str(environment.helper),
        ],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        env=environment.process_environment,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stderr == ""
    response = json.loads(completed.stdout)
    assert response["contract"] == "ldvh-doctor/1"
    assert response["status"] == "ready"
    assert response["distribution"]["version"] == importlib.metadata.version("ld-vibe-harness")
    assert response["configuration"]["scope_status"] == "governed_single"
    assert all(item["state"] == "available" for item in response["integration_surfaces"])
    assert "documentation" not in response


def _assert_native_git_hook_runners(environment: InstalledEnvironment) -> None:
    for runner in (environment.commit_msg_runner, environment.git_hook_manager):
        completed = subprocess.run(
            [str(runner), "--help"],
            cwd=environment.root,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            env=environment.process_environment,
            check=False,
        )
        assert completed.returncode == 0, (runner, completed.stdout, completed.stderr)
        assert completed.stdout


def _assert_uninstalled(environment: InstalledEnvironment) -> None:
    assert not environment.helper.exists()
    assert not environment.doctor.exists()
    assert not environment.context_recovery_runner.exists()
    assert not environment.commit_msg_runner.exists()
    assert not environment.git_hook_manager.exists()
    assert not (environment.purelib / "ldvh").exists()
    assert not tuple(environment.purelib.glob("ld_vibe_harness-*.dist-info"))
    completed = subprocess.run(
        [
            str(environment.python),
            "-c",
            (
                "import importlib.metadata, importlib.util; "
                "assert importlib.util.find_spec('ldvh') is None; "
                "\ntry: importlib.metadata.distribution('ld-vibe-harness')"
                "\nexcept importlib.metadata.PackageNotFoundError: pass"
                "\nelse: raise AssertionError('distribution remains installed')"
            ),
        ],
        cwd=environment.root,
        env=environment.process_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)


def test_direct_wheel_replaces_old_record_repairs_tampering_and_uninstalls(
    release_artifacts: ReleaseArtifacts,
    tmp_path: Path,
) -> None:
    environment = _create_installed_environment(tmp_path / "direct-environment")
    decoy = tmp_path / "decoy-cwd"
    (decoy / "specs").mkdir(parents=True)
    (decoy / "specs" / "00-理念与构成.md").write_text("not the installed source\n", encoding="utf-8")

    _pip(environment, "install", "--no-deps", str(release_artifacts.old_wheel))
    old_marker = environment.purelib / "ldvh" / "legacy_release_marker.py"
    assert old_marker.is_file()
    _assert_version(
        environment,
        decoy,
        release_artifacts.old_version,
        release_artifacts.old_snapshot_sha256,
    )

    _pip(environment, "install", "--no-deps", "--upgrade", str(release_artifacts.current_wheel))
    assert not old_marker.exists()
    assert len(tuple(environment.purelib.glob("ld_vibe_harness-*.dist-info"))) == 1
    _assert_version(
        environment,
        decoy,
        release_artifacts.current_version,
        release_artifacts.current_snapshot_sha256,
    )

    manifest = environment.purelib / "ldvh" / "_rule_snapshot" / "manifest.json"
    original_manifest = manifest.read_bytes()
    manifest.write_bytes(original_manifest + b"tampered")
    unavailable = _cli(environment, decoy, "capabilities", None, "", expected_exit=5)
    assert unavailable["outcome"] == "unavailable"
    _pip(environment, "install", "--no-deps", "--force-reinstall", str(release_artifacts.current_wheel))
    assert manifest.read_bytes() == original_manifest
    _assert_version(
        environment,
        decoy,
        release_artifacts.current_version,
        release_artifacts.current_snapshot_sha256,
    )
    _assert_context_recovery_runner(environment, tmp_path / "direct-context-recovery")
    _assert_doctor_runner(environment, tmp_path / "direct-doctor")
    _assert_native_git_hook_runners(environment)

    _exercise_operation_matrix(
        environment,
        tmp_path / "direct-matrix",
        release_artifacts.current_version,
        release_artifacts.current_snapshot_sha256,
    )
    _pip(environment, "uninstall", "-y", "ld-vibe-harness")
    _assert_uninstalled(environment)


def test_sdist_derived_wheel_runs_the_same_process_matrix_and_uninstalls(
    release_artifacts: ReleaseArtifacts,
    tmp_path: Path,
) -> None:
    environment = _create_installed_environment(tmp_path / "sdist-environment")
    _pip(environment, "install", "--no-deps", str(release_artifacts.sdist_wheel))
    _assert_version(
        environment,
        tmp_path,
        release_artifacts.current_version,
        release_artifacts.current_snapshot_sha256,
    )
    _assert_context_recovery_runner(environment, tmp_path / "sdist-context-recovery")
    _assert_doctor_runner(environment, tmp_path / "sdist-doctor")
    _assert_native_git_hook_runners(environment)
    _exercise_operation_matrix(
        environment,
        tmp_path / "sdist-matrix",
        release_artifacts.current_version,
        release_artifacts.current_snapshot_sha256,
    )
    _pip(environment, "uninstall", "-y", "ld-vibe-harness")
    _assert_uninstalled(environment)
