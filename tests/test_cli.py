from importlib.metadata import version
from pathlib import Path
import tomllib

from uv_kernel import __version__
from uv_kernel.cli import main, parser


def test_package_and_cli_versions_match_installed_metadata(capsys):
    metadata_version = version("uv-kernel-manager")
    project_version = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    assert metadata_version == project_version
    assert __version__ == metadata_version

    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert capsys.readouterr().out.strip() == f"uv-kernel {metadata_version}"


def test_top_level_help_explains_ownership(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "ownership metadata" in capsys.readouterr().out


def test_clean_is_safe_without_yes(monkeypatch, capsys):
    monkeypatch.setattr("uv_kernel.cli.owned_kernels", lambda: [{"name": "uv-kernel-x", "project_path": "/gone"}])
    monkeypatch.setattr("uv_kernel.cli.stale", lambda items: items)
    assert main(["clean"]) == 0
    assert "--yes" in capsys.readouterr().out
