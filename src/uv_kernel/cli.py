"""Command line interface for uv-kernel."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import __version__
from .core import (
    UVKernelError,
    display_name,
    doctor,
    ensure_ipykernel,
    find_project,
    install,
    matching,
    owned_kernels,
    remove,
    stale,
)

DESCRIPTION = """
Manage Jupyter kernels for uv-managed Python environments.

Register a project's uv `.venv` with the Jupyter installation you already use.
Only kernels carrying uv-kernel's ownership metadata are ever changed or removed.
"""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="uv-kernel", description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  uv-kernel register\n  uv-kernel --json list\n  uv-kernel clean --yes")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--json", action="store_true", dest="json_output", help="Output machine-readable JSON.")
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")
    register = sub.add_parser("register", help="Register the current uv project as a Jupyter kernel.",
        description="Adds ipykernel as a development dependency by default and writes a standard user kernelspec.")
    register.add_argument("--no-add-ipykernel", action="store_true", help="Do not run `uv add --dev ipykernel` first.")
    naming = register.add_mutually_exclusive_group()
    naming.add_argument("--name", metavar="NAME", help="Use NAME as the kernel label instead of the suggested label.")
    naming.add_argument("--yes", action="store_true", help="Accept the suggested kernel label without prompting.")
    sub.add_parser("unregister", help="Remove this project's uv-kernel-owned kernel.",
        description="Removes only kernels marked as owned by uv-kernel for the current project.")
    sub.add_parser("list", help="List every kernel owned by uv-kernel.")
    sub.add_parser("status", help="Show this project's uv-kernel registration status.")
    sub.add_parser("refresh", help="Recreate this project's owned kernel with current settings.",
        description="Updates the spec for the current .venv; it never touches other kernels.")
    clean = sub.add_parser("clean", help="Find stale uv-kernel-owned kernels safely.",
        description="Reports kernels whose project or .venv interpreter is gone. Nothing is deleted without --yes.")
    clean.add_argument("--yes", action="store_true", help="Remove the stale kernels reported by clean.")
    sub.add_parser("doctor", help="Diagnose uv, the current project, and Jupyter kernel paths.")
    return p


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    if isinstance(value, list):
        if not value:
            print("No uv-kernel-owned kernels found.")
        for item in value:
            print(f"{item['name']}: {item.get('display_name', '')} — {item.get('project_path', '')}")
    elif isinstance(value, dict):
        for key, item in value.items(): print(f"{key}: {item}")
    else: print(value)


def choose_kernel_name(default: str) -> str:
    """Prompt for a kernel label, accepting the suggested label on Enter."""
    try:
        response = input(
            f"Register kernel as: {default}\n"
            "Press Enter to continue, or enter a custom name: "
        ).strip()
    except EOFError as exc:
        raise UVKernelError("No kernel name was provided. Use --yes or --name for non-interactive use.") from exc
    return response or default


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "list":
            emit(owned_kernels(), args.json_output)
            return 0
        
        if args.command == "clean":
            items = stale(owned_kernels())
            if args.yes:
                removed = remove(items)
                emit({"removed": removed, "count": len(removed)}, args.json_output)
            else:
                emit(items, args.json_output)
                if not args.json_output and items: 
                    print("Run `uv-kernel clean --yes` to remove these kernels.")
            return 0
        
        if args.command == "doctor":
            try: 
                project = find_project()
            except UVKernelError: 
                project = None
            emit(doctor(project), args.json_output)
            return 0
        
        project = find_project()
        if args.command == "register":
            suggested_name = display_name(project)
            if args.name:
                kernel_display_name = args.name
            elif args.yes:
                kernel_display_name = suggested_name
            elif args.json_output:
                raise UVKernelError("Use --yes or --name with --json register.")
            else:
                kernel_display_name = choose_kernel_name(suggested_name)
            if not args.no_add_ipykernel:
                ensure_ipykernel(project)
            result = install(project, kernel_display_name=kernel_display_name)
            emit({"registered": result}, args.json_output)
            return 0
        
        if args.command == "unregister":
            removed = remove(matching(project))
            emit({"removed": removed, "count": len(removed)}, args.json_output)
            return 0
        
        if args.command == "status":
            items = matching(project)
            result = {"project": str(project.root), "registered": bool(items), "kernels": items}
            emit(result, args.json_output)
            return 0 if items else 1
        
        if args.command == "refresh":
            remove(matching(project))
            result = install(project)
            emit({"refreshed": result}, args.json_output)
            return 0
        
    except UVKernelError as exc:
        if args.json_output: 
            print(json.dumps({"error": str(exc)}))
        else: 
            print(f"uv-kernel: error: {exc}", file=sys.stderr)
        return 2
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
