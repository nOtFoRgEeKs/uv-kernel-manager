#!/usr/bin/env python3
"""Validate the package version used by the continuous-delivery workflow."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from packaging.version import InvalidVersion, Version


CHANGELOG_PATH = Path("CHANGELOG.md")


def version_from_toml(contents: str, source: str) -> str:
    try:
        version = tomllib.loads(contents)["project"]["version"]
    except (KeyError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Could not read [project].version from {source}: {error}") from error
    if not isinstance(version, str):
        raise ValueError(f"{source} has a non-string [project].version.")
    try:
        parsed = Version(version)
    except InvalidVersion as error:
        raise ValueError(
            f"{source} has invalid PEP 440 release version {version!r}."
        ) from error
    if parsed.local is not None:
        raise ValueError(
            f"{source} has local version {version!r}; local versions cannot be published to PyPI."
        )
    if version != str(parsed):
        raise ValueError(
            f"{source} has non-canonical PEP 440 version {version!r}; use {str(parsed)!r}."
        )
    return version


def version_from_file(path: Path) -> str:
    return version_from_toml(path.read_text(encoding="utf-8"), str(path))


def version_from_git_ref(ref: str) -> str | None:
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:pyproject.toml"],
        capture_output=True,
        text=True,
    )
    if exists.returncode:
        # This supports the one-time bootstrap of a repository whose main
        # branch did not yet contain a Python project. In the normal case,
        # main has a manifest and its version must be exceeded.
        return None
    result = subprocess.run(
        ["git", "show", f"{ref}:pyproject.toml"],
        check=True,
        capture_output=True,
        text=True,
    )
    return version_from_toml(result.stdout, f"{ref}:pyproject.toml")


def changelog_notes(version: str) -> str:
    """Return the Markdown notes for a PEP 440 version."""
    try:
        changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Could not read {CHANGELOG_PATH}: {error}") from error

    heading = re.compile(
        rf"^## \[{re.escape(version)}\]\s*$",
        re.MULTILINE,
    )
    match = heading.search(changelog)
    if match is None:
        raise ValueError(
            f"{CHANGELOG_PATH} must contain a section headed "
            f"'## [{version}]'."
        )

    next_heading = re.compile(r"^##\s+", re.MULTILINE).search(changelog, match.end())
    notes = changelog[match.end() : next_heading.start() if next_heading else len(changelog)].strip()
    if not notes:
        raise ValueError(f"The [{version}] changelog section must contain release notes.")
    return notes + "\n"


def changelog_changed_since(base_ref: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", f"{base_ref}...HEAD", "--", str(CHANGELOG_PATH)]
    )
    return result.returncode == 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument("--write-release-notes", type=Path, metavar="PATH")
    parser.add_argument("--base-ref", help="Require the version to be greater than this ref's version")
    parser.add_argument(
        "--require-changelog-change",
        action="store_true",
        help="Require CHANGELOG.md to differ from --base-ref",
    )
    args = parser.parse_args()

    try:
        version = version_from_file(Path("pyproject.toml"))
        notes = changelog_notes(version)
        if args.base_ref:
            base_version = version_from_git_ref(args.base_ref)
            if base_version is not None and Version(version) <= Version(base_version):
                raise ValueError(
                    f"Release version {version} must be greater than the base version {base_version}."
                )
            if args.require_changelog_change and not changelog_changed_since(args.base_ref):
                raise ValueError(f"{CHANGELOG_PATH} must be updated for a release pull request.")
        elif args.require_changelog_change:
            raise ValueError("--require-changelog-change requires --base-ref.")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Release version validation failed: {error}", file=sys.stderr)
        return 1

    if args.write_release_notes:
        args.write_release_notes.write_text(notes, encoding="utf-8")
    if args.print_version:
        print(version)
    else:
        print(f"Release version {version} is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
