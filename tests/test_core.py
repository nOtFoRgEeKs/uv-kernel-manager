
import pytest

from uv_kernel.core import (
    Project,
    UVKernelError,
    find_project,
    kernel_id,
    owned,
    spec_data,
)


def test_find_project_uses_metadata_name_and_venv(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'my-project'\n")
    nested = tmp_path / "a" / "b"; nested.mkdir(parents=True)
    project = find_project(nested)
    assert project.root == tmp_path
    assert project.name == "my-project"
    assert project.python == tmp_path / ".venv/bin/python"


def test_find_project_falls_back_to_directory_name(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 88\n")
    assert find_project(tmp_path).name == tmp_path.name


def test_find_project_requires_manifest(tmp_path):
    with pytest.raises(UVKernelError, match="No pyproject"):
        find_project(tmp_path)


def test_kernel_id_is_stable_and_path_specific(tmp_path):
    one = Project(tmp_path / "one", "My Project", tmp_path / "python")
    two = Project(tmp_path / "two", "My Project", tmp_path / "python")
    assert kernel_id(one).startswith("uv-kernel-my-project-")
    assert kernel_id(one) != kernel_id(two)


def test_ownership_requires_structured_metadata(tmp_path, monkeypatch):
    project = Project(tmp_path, "demo", tmp_path / "python")
    monkeypatch.setattr("uv_kernel.core.display_name", lambda _: "Python 3.14 (demo)")
    data = {"spec": spec_data(project)}
    assert owned(data)
    assert not owned({"spec": {"metadata": {"uv-kernel": "yes"}}})
