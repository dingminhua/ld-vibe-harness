"""Setuptools commands that freeze one verified rule snapshot into release artifacts."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

USER_DOCUMENTS = ("specs/attachments/09.Att.01-环境接入面.md",)
USER_DOCUMENT_DIRECTORY = "_user_docs"
INTEGRATION_ASSET_DIRECTORY = "_integration_assets"
INTEGRATION_ASSET_FILES = ("skill/SKILL.md",)


def _integration_asset_paths() -> tuple[str, ...]:
    icons = tuple(sorted(path.name for path in (ROOT / "icons").glob("*.png")))
    return (*INTEGRATION_ASSET_FILES, *(f"icons/{name}" for name in icons))

from ldvh.rule_snapshot import SNAPSHOT_DIRECTORY, snapshot_plan_for_source, write_snapshot  # noqa: E402


class build_py(_build_py):
    def run(self) -> None:
        shutil.rmtree(self.build_lib, ignore_errors=True)
        super().run()
        plan = snapshot_plan_for_source(ROOT, self.distribution.get_version())
        destination = Path(self.build_lib) / "ldvh" / SNAPSHOT_DIRECTORY
        write_snapshot(plan, destination)
        user_document_destination = Path(self.build_lib) / "ldvh" / USER_DOCUMENT_DIRECTORY
        user_document_destination.mkdir(parents=True, exist_ok=True)
        for relative in USER_DOCUMENTS:
            shutil.copy2(ROOT / relative, user_document_destination / Path(relative).name)
        self._ldvh_snapshot_outputs = [str(destination / item.path) for item in plan.files] + [
            str(destination / "manifest.json")
        ]
        self._ldvh_user_document_outputs = [
            str(user_document_destination / Path(relative).name) for relative in USER_DOCUMENTS
        ]
        integration_destination = Path(self.build_lib) / "ldvh" / INTEGRATION_ASSET_DIRECTORY
        for relative in _integration_asset_paths():
            target = integration_destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        self._ldvh_integration_asset_outputs = [
            str(integration_destination / relative) for relative in _integration_asset_paths()
        ]

    def get_outputs(self, include_bytecode: bool = True) -> list[str]:
        return [
            *super().get_outputs(include_bytecode=include_bytecode),
            *getattr(self, "_ldvh_snapshot_outputs", ()),
            *getattr(self, "_ldvh_user_document_outputs", ()),
            *getattr(self, "_ldvh_integration_asset_outputs", ()),
        ]


class sdist(_sdist):
    def _snapshot_plan(self):
        plan = getattr(self, "_ldvh_snapshot_plan", None)
        if plan is None:
            plan = snapshot_plan_for_source(ROOT, self.distribution.get_version())
            self._ldvh_snapshot_plan = plan
        return plan

    def make_distribution(self) -> None:
        self.filelist.files = [
            path for path in self.filelist.files if not path.startswith("code/scripts/")
        ]
        for item in self._snapshot_plan().files:
            self.filelist.append(item.path)
        for relative in USER_DOCUMENTS:
            self.filelist.append(relative)
        for relative in _integration_asset_paths():
            self.filelist.append(relative)
        self.filelist.sort()
        self.filelist.remove_duplicates()
        super().make_distribution()

    def make_release_tree(self, base_dir: str, files: list[str]) -> None:
        super().make_release_tree(base_dir, files)
        write_snapshot(
            self._snapshot_plan(),
            Path(base_dir) / "code/ldvh" / SNAPSHOT_DIRECTORY,
        )


setup(cmdclass={"build_py": build_py, "sdist": sdist})
