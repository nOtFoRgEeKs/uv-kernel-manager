"""Project discovery and safe Jupyter kernelspec operations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jupyter_client.kernelspec import KernelSpecManager

from . import __version__

OWNER_KEY = "uv-kernel"


class UVKernelError(RuntimeError):
    """A recoverable command error which should be shown to the user."""


@dataclass(frozen=True)
class Project:
    root: Path
    name: str
    python: Path


def find_project(start: Path | None = None) -> Project:
    """Find the closest enclosing uv project and its project-local interpreter."""
    directory = (start or Path.cwd()).resolve()
    for candidate in (directory, *directory.parents):
        manifest = candidate / "pyproject.toml"
        if manifest.is_file():
            try:
                data = tomllib.loads(manifest.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as exc:
                raise UVKernelError(f"Cannot read {manifest}: {exc}") from exc
            name = data.get("project", {}).get("name") or candidate.name
            if not isinstance(name, str) or not name.strip():
                name = candidate.name
            python = candidate / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            return Project(candidate, name, python)
    raise UVKernelError("No pyproject.toml found in this directory or its parents.")


def kernel_id(project: Project) -> str:
    """A stable, collision-resistant Jupyter kernelspec identifier."""
    slug = re.sub(r"[^a-z0-9]+", "-", project.name.lower()).strip("-") or "project"
    digest = hashlib.sha256(str(project.root).encode()).hexdigest()[:10]
    return f"uv-kernel-{slug}-{digest}"


def python_version(python: Path) -> str:
    try:
        result = subprocess.run(
            [str(python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise UVKernelError(f"Could not run project Python at {python}: {exc}") from exc
    return result.stdout.strip()


def display_name(project: Project) -> str:
    return f"Python {python_version(project.python)} ({project.name})"


def ensure_ipykernel(project: Project) -> None:
    """Ask uv to add ipykernel as a development dependency."""
    try:
        subprocess.run(["uv", "add", "--dev", "ipykernel"], cwd=project.root, check=True)
    except FileNotFoundError as exc:
        raise UVKernelError("uv was not found on PATH; install uv before registering.") from exc
    except subprocess.CalledProcessError as exc:
        raise UVKernelError("uv could not add the development dependency ipykernel.") from exc


def spec_data(project: Project) -> dict[str, Any]:
    return {
        "argv": [str(project.python), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": display_name(project),
        "language": "python",
        "metadata": {OWNER_KEY: {
            "version": __version__, "project_path": str(project.root),
            "project_name": project.name,
        }},
    }


def owned(spec: dict[str, Any]) -> bool:
    return isinstance(spec.get("spec", {}).get("metadata", {}).get(OWNER_KEY), dict)


def owned_kernels(manager: KernelSpecManager | None = None) -> list[dict[str, Any]]:
    manager = manager or KernelSpecManager()
    results = []
    for name, data in manager.get_all_specs().items():
        if owned(data):
            meta = data["spec"]["metadata"][OWNER_KEY]
            results.append({
                "name": name, "display_name": data["spec"].get("display_name"),
                "resource_dir": data.get("resource_dir"), "project_path": meta.get("project_path"),
                "project_name": meta.get("project_name"), "version": meta.get("version"),
            })
    return sorted(results, key=lambda item: item["name"])


def install(project: Project, manager: KernelSpecManager | None = None) -> dict[str, Any]:
    if not project.python.is_file():
        raise UVKernelError(f"No project interpreter found at {project.python}. Run `uv sync` first.")
    manager = manager or KernelSpecManager()
    name = kernel_id(project)
    with tempfile.TemporaryDirectory(prefix="uv-kernel-") as temp:
        Path(temp, "kernel.json").write_text(json.dumps(spec_data(project), indent=2) + "\n", encoding="utf-8")
        manager.install_kernel_spec(temp, kernel_name=name, user=True, replace=True)
    return {"name": name, "display_name": display_name(project), "project_path": str(project.root)}


def matching(project: Project, manager: KernelSpecManager | None = None) -> list[dict[str, Any]]:
    return [item for item in owned_kernels(manager) if item["project_path"] == str(project.root)]


def remove(items: list[dict[str, Any]], manager: KernelSpecManager | None = None) -> list[str]:
    manager = manager or KernelSpecManager()
    removed: list[str] = []
    for item in items:
        manager.remove_kernel_spec(item["name"])
        removed.append(item["name"])
    return removed


def stale(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if not item.get("project_path") or not Path(item["project_path"]).is_dir()
            or not Path(item["project_path"], ".venv", "Scripts/python.exe" if os.name == "nt" else "bin/python").is_file()]


def doctor(project: Project | None) -> dict[str, Any]:
    details: dict[str, Any] = {
        "uv": shutil.which("uv"), "jupyter_paths": KernelSpecManager().kernel_dirs,
        "python": sys.executable,
    }
    if project:
        details["project"] = {
            "path": str(project.root), "name": project.name,
            "interpreter": str(project.python), "interpreter_exists": project.python.is_file()
        }
        if project.python.is_file():
            try:
                details["project"]["python_version"] = python_version(project.python)
            except UVKernelError as exc:
                details["project"]["python_error"] = str(exc)
    return details
