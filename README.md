# uv-kernel-manager

`uv-kernel-manager` registers the Python environments created by
[`uv`](https://docs.astral.sh/uv/) projects as Jupyter kernels. It is designed
for a single JupyterLab installation shared across many projects, each with
its own project-local `.venv`.

The PyPI distribution is `uv-kernel-manager`; the command is `uv-kernel`; the
Python package is `uv_kernel`.

## How it works

```
JupyterLab installation
        │
        ├── Python 3.12 (analytics) ──> analytics/.venv/bin/python
        └── Python 3.13 (forecasting) ─> forecasting/.venv/bin/python
```

Run `uv-kernel register` from a uv project to create a standard, user-level
Jupyter kernelspec pointing at that project's interpreter. The command suggests
a label in the form `Python <major.minor> (<project-name>)`, such as
`Python 3.13 (forecasting)`, and lets you accept it or provide a label that is
more meaningful to you.

The tool manages kernelspecs only. It does not install, start, configure, or
upgrade JupyterLab; it also does not create or otherwise manage your uv
projects or their virtual environments.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) on your `PATH`
- A uv project with a `pyproject.toml` and a synchronized `.venv` (`uv sync`)
- JupyterLab or another Jupyter frontend installed wherever you normally run it

`register` adds `ipykernel` to the current project's development dependencies
by default. Use `--no-add-ipykernel` only when it is already installed or you
do not want the command to change project dependencies.

## Installation

Install the tool permanently with uv:

```bash
uv tool install uv-kernel-manager
```

Then run the `uv-kernel` command from a project directory:

```bash
cd path/to/forecasting
uv sync
uv-kernel register
jupyter lab
```

During registration, the tool shows the suggested Jupyter label:

```text
Register kernel as: Python 3.13 (forecasting)
Press Enter to continue, or enter a custom name:
```

Press Enter to use it, or type a custom label. For scripts and other
non-interactive usage, accept the suggestion with `--yes` or set it explicitly
with `--name`:

```bash
uv-kernel register --yes
uv-kernel register --name "Forecasting — production"
```

To run without installing it, use `uvx`:

```bash
uvx uv-kernel-manager register
uvx uv-kernel-manager status
```

## Commands

| Command | Purpose |
| --- | --- |
| `uv-kernel register` | Prompt for a label and add the current project's `.venv` as a Jupyter kernel. |
| `uv-kernel register --yes` | Register with the suggested label without prompting. |
| `uv-kernel register --name "NAME"` | Register with an explicit Jupyter label. |
| `uv-kernel status` | Show whether the current project is registered. |
| `uv-kernel refresh` | Recreate the current project's kernel with its current interpreter and settings. |
| `uv-kernel unregister` | Remove the current project's managed kernel. |
| `uv-kernel list` | List every kernel managed by this tool. |
| `uv-kernel clean` | Report managed kernels whose project or interpreter no longer exists. |
| `uv-kernel clean --yes` | Remove the stale managed kernels reported by `clean`. |
| `uv-kernel doctor` | Show diagnostic information about uv, the project, and Jupyter kernel locations. |

Use `--json` with reporting commands when scripting, for example:

```bash
uv-kernel --json list
uv-kernel --json status
```

For a non-interactive JSON registration, include either `--yes` or `--name`:

```bash
uv-kernel --json register --yes
uv-kernel --json register --name "Forecasting — production"
```

## Safety and ownership

Every kernel created by this tool includes a structured `metadata.uv-kernel`
ownership record. `unregister`, `refresh`, and `clean` act only on kernels
with that record; manually installed kernels and kernels managed by other
tools are left untouched. Kernel directory names also begin with `uv-kernel-`,
but the metadata marker—not the directory name—is the ownership check.

`clean` is intentionally non-destructive unless you explicitly pass `--yes`.

## Build from source

To build the package locally, clone the repository and install its development
dependencies:

```bash
uv sync --dev
uv build
```

The wheel and source distribution are written to `dist/`. To install the local
checkout as a tool, run:

```bash
uv tool install .
```

## Development

Run the test suite and validate built package metadata before contributing:

```bash
uv run pytest
uv run twine check dist/*
```

You can also run the command directly from the checkout:

```bash
uv run uv-kernel --help
```

## Release workflow

`main` represents released software. Normal development flows from feature
branches into `develop`; those changes are validated by CI only. A release is
created exclusively when the repository's `develop` branch is merged into the
protected `main` branch through a pull request. Direct pushes to `main`, pushes
to `develop`, feature branches, and manual GitHub releases do not publish to
PyPI.

Before opening a `develop` → `main` pull request, update `[project].version` in
`pyproject.toml` to a new, canonical public [PEP 440](https://peps.python.org/pep-0440/)
version. For example, use `0.1.2` for the next patch release or `0.2.0a1` for
an alpha release. The CI check on that pull request rejects an unchanged,
lower, malformed, or local version before it can merge.

The same pull request must update `CHANGELOG.md`. Use one section per release
in this form:

```markdown
## [0.2.0a1]

### Added

- A user-visible change.
```

The GitHub Release title is the release tag (for example, `v0.2.0a1`), and the
section body becomes its release notes. This keeps the public changelog and
GitHub Release notes identical. The quality gate rejects a release PR if the
matching version section is missing, empty, or `CHANGELOG.md` did not change
from `main`.

After the pull request is merged, the release workflow serially:

1. validates the exact merge commit and its version;
2. rejects an existing Git tag or PyPI release for that version;
3. runs the locked test, build, and package-metadata checks;
4. creates the annotated tag `v<version>`;
5. publishes the wheel and source distribution to PyPI with Trusted Publishing;
6. creates a GitHub Release using the title and notes from `CHANGELOG.md`.

The workflow does not overwrite PyPI releases. If a stale version, tag, or
existing PyPI release is detected, it fails before publishing. Releases are
also queued one at a time to prevent concurrent publication attempts.

### One-time repository configuration

1. Protect `main`: require pull requests and the CI checks, and prevent direct
   pushes. Restrict merges to the maintainers who approve releases.
2. In PyPI, configure a Trusted Publisher for this repository with workflow
   file `.github/workflows/release.yaml` and environment `pypi`.
3. In GitHub, create the protected `pypi` environment (recommended) and limit
   its deployment approval rules to release maintainers.

If publication fails after the tag has been pushed, investigate the failure
before retrying. Do not delete or move a published release tag; the version
gate intentionally treats an existing tag as immutable.

## Contributing

Contributions are welcome. Please open an issue or pull request with a focused
change, include tests when behavior changes, and run the checks above before
submitting.
