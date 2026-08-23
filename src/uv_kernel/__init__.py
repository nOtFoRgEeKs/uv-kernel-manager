"""Manage Jupyter kernels for uv-managed projects."""

from importlib.metadata import version

# The installed distribution metadata is generated from [project].version in
# pyproject.toml, keeping that file as the only version authority.
__version__ = version("uv-kernel")
