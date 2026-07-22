"""Module: install — one-command vault-graph installer for Hermes + Trae."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def install(project: bool = False, project_dir: Path | None = None):
    """Install vault-graph skill into Hermes + Trae profiles."""

    if project:
        dests = [
            (project_dir or Path.cwd()) / ".hermes" / "skills" / "vault" / "vault-graph" / "SKILL.md",
            (project_dir or Path.cwd()) / ".trae" / "builtin_skills" / "vault-graph" / "SKILL.md",
        ]
    else:
        dests = [
            Path.home() / ".hermes" / "skills" / "vault" / "vault-graph" / "SKILL.md",
            Path.home() / ".trae" / "builtin_skills" / "vault-graph" / "SKILL.md",
        ]

    # Find source skill file
    src = Path(__file__).parent.parent.parent / "skills" / "vault" / "vault-graph" / "SKILL.md"
    if not src.exists():
        src = Path(__file__).parent.parent.parent / "skills-all" / "vault" / "vault-graph" / "SKILL.md"

    if not src.exists():
        print("error: SKILL.md not found", file=sys.stderr)
        sys.exit(1)

    for dest in dests:
        dest.parent.mkdir(parents=True, exist_ok=True)

        if src.resolve() == dest.resolve():
            print(f"  Already installed: {dest}")
            continue

        shutil.copy2(src, dest)
        print(f"  Installed: {dest}")

        # Copy references if present
        refs_src = src.parent / "references"
        if refs_src.is_dir():
            refs_dest = dest.parent / "references"
            if refs_dest.exists():
                shutil.rmtree(refs_dest)
            shutil.copytree(refs_src, refs_dest)
            print(f"  References: {refs_dest}")

    print(f"\nDone! Skill installed for Hermes + Trae.")
    print("  Hermes: type /vault-graph or 'graph vault'")
    print("  Trae:   type /vault-graph or 'graph vault'")


def uninstall():
    """Remove vault-graph skill from all platforms."""
    paths = [
        Path.home() / ".hermes" / "skills" / "vault" / "vault-graph",
        Path.home() / ".hermes" / "skills" / "vault-graph",
        Path.home() / ".trae" / "builtin_skills" / "vault-graph",
    ]
    for p in paths:
        if p.exists():
            shutil.rmtree(p)
            print(f"  Removed: {p}")
    print("Done.")
