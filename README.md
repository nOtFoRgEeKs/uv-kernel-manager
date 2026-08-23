# uv-kernel

`uv-kernel` manages Jupyter kernels whose Python interpreters live in
[`uv`](https://docs.astral.sh/uv/) project environments. It is intended for a
central JupyterLab installation with separate, project-local `.venv`
environments.

It writes ordinary Jupyter kernelspecs and only changes kernels carrying its
`metadata.uv-kernel` ownership record. A project named `fraud-model` using
Python 3.14 is displayed exactly as `Python 3.14 (fraud-model)`.

## Install

Install the command-line tool with uv:

```bash
uv tool install uv-kernel
```

Or use pip in an environment of your choice:

```bash
python -m pip install uv-kernel
```

For local development, install the checkout as a tool:

```bash
uv tool install .
```

Before the first public release, replace
`REPLACE_WITH_YOUR_USERNAME` in `pyproject.toml` with the GitHub user or
organization that owns the repository.

## Typical workflow

From a uv project directory (one containing `pyproject.toml`):

```bash
uv-kernel register
jupyter lab
```

`register` runs `uv add --dev ipykernel` by default, then registers the
project's `.venv/bin/python`. Use `--no-add-ipykernel` when it is already
available or dependency changes are not wanted.

```bash
uv-kernel status
uv-kernel refresh
uv-kernel unregister
uv-kernel list
uv-kernel clean              # report stale owned kernels
uv-kernel clean --yes        # remove stale owned kernels
uv-kernel doctor
```

All reporting commands support `--json`, for example
`uv-kernel --json list`. `clean` deliberately never deletes anything without
`--yes`.

## Ownership and safety

Kernel directory names start with `uv-kernel-`, but the actual safety check is
the structured `metadata.uv-kernel` marker in `kernel.json`. `unregister`,
`refresh`, and `clean` only operate on specs with that marker. Thus manually
installed and other tool-managed kernels are left untouched.

## Development

```bash
uv sync --dev
uv run pytest
uv build
```

## Releases

The CI workflow runs tests, builds distributions, and checks their package
metadata for every pull request and push to `main`. Publishing happens only
after a GitHub Release is **published**. The release workflow accepts semantic
version tags in the form `v0.1.0`, `v0.1.1`, or `v1.0.0`, plus PyPI
pre-releases such as `v0.1.0rc1`, `v0.1.0a1`, and `v0.1.0b1`. It refuses to
publish unless the tag exactly matches `[project].version` in `pyproject.toml`
(for example, `v0.1.0rc1` and `0.1.0rc1`).

It uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/),
so no PyPI API token is stored in GitHub.

### First-time PyPI setup

Create a pending publisher on PyPI (or a trusted publisher in an existing PyPI
project) with the following values:

- Owner: your GitHub user or organization
- Repository: `uv-kernel`
- Workflow: `release.yaml`
- Environment: `pypi`

The workflow only needs `contents: read` and `id-token: write`; do not create
or store a PyPI token in the repository.

### Publishing a release

1. Update the package version in `pyproject.toml` (for example with `uv version
   --bump patch`) and refresh the lock file. For the initial release, the
   current version is already `0.1.0`, so do not bump it first.
2. Commit and push that version change to `main`; let CI pass.
3. In GitHub, choose **Releases** → **Draft a new release**, create or select
   the matching tag (for example `v0.1.1`) at the approved `main` commit, and
   click **Publish release**.

For a later patch release, the equivalent GitHub CLI command is:

```bash
uv version --bump patch
uv lock
git add pyproject.toml uv.lock
git commit -m "Release v0.1.1"
git push origin main
gh release create v0.1.1 --target main --title "v0.1.1" --generate-notes
```

Publishing the GitHub Release runs the validation, test, build, and PyPI upload
for that exact tag. A tag push by itself does not publish anything.
