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

from ldvh.rule_snapshot import SNAPSHOT_DIRECTORY, snapshot_plan_for_source, write_snapshot  # noqa: E402


class build_py(_build_py):
    def run(self) -> None:
        shutil.rmtree(self.build_lib, ignore_errors=True)
        super().run()
        plan = snapshot_plan_for_source(ROOT, self.distribution.get_version())
        destination = Path(self.build_lib) / "ldvh" / SNAPSHOT_DIRECTORY
        write_snapshot(plan, destination)
        self._ldvh_snapshot_outputs = [str(destination / item.path) for item in plan.files] + [
            str(destination / "manifest.json")
        ]

    def get_outputs(self, include_bytecode: bool = True) -> list[str]:
        return [
            *super().get_outputs(include_bytecode=include_bytecode),
            *getattr(self, "_ldvh_snapshot_outputs", ()),
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
            path for path in self.filelist.files if not path.startswith(("code/plugins/", "code/scripts/"))
        ]
        for item in self._snapshot_plan().files:
            self.filelist.append(item.path)
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
