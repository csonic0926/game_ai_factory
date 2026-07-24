#!/usr/bin/env python3
"""game_ai_factory setup — skill sync and game-repo routing link.

Dependency-free. Two subcommands:

  sync   Install/refresh factory-provided skills into agent-harness skill
         directories. Symlink-first: with symlinks, `git pull` on this
         factory checkout IS the skill update and no re-run is needed.
         `--copy` exists for filesystems/harnesses without symlink support;
         copied skills are tracked in a per-target manifest and re-`sync`
         refreshes them. Only entries owned by this factory are ever
         touched.

  link   Write the harness-agnostic Game AI Factory routing block into a
         game repo: a git-ignored local pointer file with this machine's
         factory path, a managed section in the repo's AGENTS.md, and a
         CLAUDE.md pointer if the repo has none. Safe to re-run; the
         managed section is replaced between markers, never duplicated.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

FACTORY_ROOT = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SKILL_TARGETS = [
    os.path.expanduser("~/.claude/skills"),
    os.path.expanduser("~/.codex/skills"),
]

MANIFEST_NAME = ".game_ai_factory_manifest.json"
POINTER_REL_PATH = os.path.join("design", "AI_FACTORY.local.md")
BLOCK_BEGIN = "<!-- game_ai_factory:routing:begin -->"
BLOCK_END = "<!-- game_ai_factory:routing:end -->"


def factory_version(factory_root):
    try:
        out = subprocess.run(
            ["git", "-C", factory_root, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except OSError:
        pass
    return "unknown"


def discover_skills(factory_root):
    """Return [(skill_name, absolute_skill_dir)] for every
    <factory>/<dept>/skills/<name>/SKILL.md."""
    found = []
    for dept in sorted(os.listdir(factory_root)):
        skills_dir = os.path.join(factory_root, dept, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for name in sorted(os.listdir(skills_dir)):
            skill_dir = os.path.join(skills_dir, name)
            if os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
                found.append((name, skill_dir))
    return found


def is_factory_owned_link(path, factory_root):
    if not os.path.islink(path):
        return False
    resolved = os.path.realpath(path)
    root = os.path.realpath(factory_root)
    return resolved == root or resolved.startswith(root + os.sep)


def load_manifest(target_dir):
    manifest_path = os.path.join(target_dir, MANIFEST_NAME)
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            pass
    return {"factory_root": FACTORY_ROOT, "skills": {}}


def save_manifest(target_dir, manifest):
    manifest_path = os.path.join(target_dir, MANIFEST_NAME)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def sync_skills(factory_root, targets, copy=False, dry_run=False):
    """Install/refresh factory skills into each existing target directory.

    Returns a list of human-readable report lines."""
    report = []
    skills = discover_skills(factory_root)
    if not skills:
        report.append("no factory skills found (nothing under */skills/*/SKILL.md)")
        return report

    seen_real = set()
    version = factory_version(factory_root)
    for target in targets:
        if not os.path.isdir(target):
            report.append("skip %s (directory does not exist)" % target)
            continue
        real = os.path.realpath(target)
        if real in seen_real:
            report.append("skip %s (same directory as an earlier target)" % target)
            continue
        seen_real.add(real)

        manifest = load_manifest(real)
        manifest["factory_root"] = factory_root
        active_names = set()
        for name, skill_dir in skills:
            active_names.add(name)
            dest = os.path.join(real, name)
            if copy:
                owned = name in manifest["skills"]
                if os.path.islink(dest) and is_factory_owned_link(dest, factory_root):
                    owned = True
                if os.path.exists(dest) and not owned:
                    report.append("CONFLICT %s exists and is not factory-owned; left untouched" % dest)
                    continue
                if not dry_run:
                    if os.path.islink(dest):
                        os.remove(dest)
                    elif os.path.isdir(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(skill_dir, dest)
                    with open(os.path.join(dest, ".factory_version"), "w", encoding="utf-8") as handle:
                        handle.write(version + "\n")
                manifest["skills"][name] = {"mode": "copy", "version": version}
                report.append("copy %s -> %s (version %s)" % (name, dest, version))
            else:
                if os.path.islink(dest):
                    if os.path.realpath(dest) == os.path.realpath(skill_dir):
                        report.append("ok %s (already linked)" % dest)
                        continue
                    if is_factory_owned_link(dest, factory_root):
                        if not dry_run:
                            os.remove(dest)
                            os.symlink(skill_dir, dest)
                        report.append("relink %s -> %s" % (dest, skill_dir))
                        continue
                    report.append("CONFLICT %s is a foreign symlink; left untouched" % dest)
                    continue
                if os.path.exists(dest):
                    if name in manifest["skills"]:
                        if not dry_run:
                            shutil.rmtree(dest) if os.path.isdir(dest) else os.remove(dest)
                            os.symlink(skill_dir, dest)
                            manifest["skills"].pop(name, None)
                        report.append("replace copy with link %s -> %s" % (dest, skill_dir))
                        continue
                    report.append("CONFLICT %s exists and is not factory-owned; left untouched" % dest)
                    continue
                if not dry_run:
                    os.symlink(skill_dir, dest)
                report.append("link %s -> %s" % (dest, skill_dir))

        # Remove entries this factory owns that no longer exist upstream.
        for entry in sorted(os.listdir(real)):
            path = os.path.join(real, entry)
            stale_link = (
                is_factory_owned_link(path, factory_root)
                and entry not in active_names
            )
            stale_copy = (
                entry in manifest["skills"] and entry not in active_names
            )
            if stale_link or stale_copy:
                if not dry_run:
                    if os.path.islink(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                    manifest["skills"].pop(entry, None)
                report.append("remove stale %s" % path)

        if not dry_run and (copy or manifest["skills"]):
            save_manifest(real, manifest)
    return report


def render_pointer_file(factory_root):
    return (
        "# Game AI Factory — local checkout pointer\n"
        "\n"
        "Machine-specific and git-ignored. Committed files must never contain\n"
        "absolute developer paths; agents resolve the factory through this file.\n"
        "\n"
        "FACTORY_ROOT: %s\n"
        "\n"
        "Regenerate: python3 <FACTORY_ROOT>/setup.py link --game-repo <this repo>\n"
        % factory_root
    )


def render_routing_block():
    return (
        BLOCK_BEGIN + "\n"
        "## Game AI Factory routing (managed block — edit via setup.py, not by hand)\n"
        "\n"
        "This game repo is production-managed by the **game_ai_factory** umbrella\n"
        "(departments: story / gameplay / asset / sound). Resolve `$FACTORY_ROOT`\n"
        "from `design/AI_FACTORY.local.md` (git-ignored, machine-specific). If that\n"
        "file is missing, ask the user for the factory path, then re-run\n"
        "`python3 $FACTORY_ROOT/setup.py link --game-repo <this repo>`.\n"
        "\n"
        "Consult the owning department **before** changing what it owns — do not\n"
        "wait for the user to name the factory:\n"
        "\n"
        "- **story** — narrative premises, world/character/chapter text, staged\n"
        "  scenes, dialogue keys. Use the `game-story-factory` skill if your\n"
        "  harness has it installed; otherwise read\n"
        "  `$FACTORY_ROOT/story/skills/game-story-factory/SKILL.md`.\n"
        "- **gameplay** — progression objectives, playable-content authoring, gap\n"
        "  repair, runtime evidence. Entry: `$FACTORY_ROOT/gameplay/AGENTS.md`.\n"
        "- **asset** — new/changed tiles, walls, props, sprites.\n"
        "  Entry: `$FACTORY_ROOT/asset/docs/AI_CALLER_LANDING.md`.\n"
        "- **sound** — new/changed SFX.\n"
        "  Entry: `$FACTORY_ROOT/sound/docs/AI_CALLER_LANDING.md`.\n"
        "\n"
        "Cross-department watchpoint: gameplay/code changes can silently erode\n"
        "story premises — e.g. adding a facility to every floor weakens a\n"
        "\"unique destination\" objective's reason to exist. When a change touches\n"
        "a fact the narrative relies on (scarcity, uniqueness, why an objective\n"
        "matters, a promised payoff), surface it and consult story before\n"
        "implementing.\n"
        "\n"
        "Factory outputs always land inside this game repo under `design/` and\n"
        "normal game paths; never write into the factory checkout from game work.\n"
        + BLOCK_END + "\n"
    )


def upsert_marked_block(text, block):
    """Insert block at the end, or replace an existing marked block in place."""
    begin = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if begin != -1 and end != -1 and end > begin:
        return text[:begin] + block + text[end + len(BLOCK_END):].lstrip("\n")
    base = text.rstrip("\n")
    if base:
        return base + "\n\n" + block
    return block


def ensure_gitignore_line(repo, line):
    gitignore = os.path.join(repo, ".gitignore")
    existing = ""
    if os.path.isfile(gitignore):
        with open(gitignore, "r", encoding="utf-8") as handle:
            existing = handle.read()
    if line in [entry.strip() for entry in existing.splitlines()]:
        return False
    body = existing
    if body and not body.endswith("\n"):
        body += "\n"
    body += "\n# Game AI Factory local pointer (machine-specific)\n" + line + "\n"
    with open(gitignore, "w", encoding="utf-8") as handle:
        handle.write(body)
    return True


CLAUDE_POINTER = (
    "# Repo agent instructions\n"
    "\n"
    "@AGENTS.md\n"
    "\n"
    "If the import above is not supported by your harness, read `AGENTS.md` in\n"
    "this repo root — it contains all agent rules, including the Game AI Factory\n"
    "routing section.\n"
)


def link_game_repo(factory_root, game_repo, dry_run=False):
    """Write pointer file, gitignore entry, AGENTS.md block, CLAUDE.md pointer."""
    report = []
    game_repo = os.path.abspath(game_repo)
    if not os.path.isdir(game_repo):
        raise SystemExit("game repo does not exist: %s" % game_repo)
    real_factory = os.path.realpath(factory_root)
    if os.path.realpath(game_repo).startswith(real_factory):
        raise SystemExit("refusing to link the factory repo to itself")

    pointer_path = os.path.join(game_repo, POINTER_REL_PATH)
    if not dry_run:
        os.makedirs(os.path.dirname(pointer_path), exist_ok=True)
        with open(pointer_path, "w", encoding="utf-8") as handle:
            handle.write(render_pointer_file(factory_root))
    report.append("write %s" % pointer_path)

    if not dry_run:
        added = ensure_gitignore_line(game_repo, POINTER_REL_PATH.replace(os.sep, "/"))
        report.append("gitignore %s" % ("add entry" if added else "entry already present"))
    else:
        report.append("gitignore ensure %s" % POINTER_REL_PATH)

    agents_path = os.path.join(game_repo, "AGENTS.md")
    existing = ""
    if os.path.isfile(agents_path):
        with open(agents_path, "r", encoding="utf-8") as handle:
            existing = handle.read()
    updated = upsert_marked_block(existing, render_routing_block())
    if not dry_run:
        with open(agents_path, "w", encoding="utf-8") as handle:
            handle.write(updated)
    report.append("%s routing block in %s" % (
        "replace" if BLOCK_BEGIN in existing else "insert", agents_path))

    claude_path = os.path.join(game_repo, "CLAUDE.md")
    if os.path.isfile(claude_path):
        report.append("keep existing %s (not modified)" % claude_path)
    else:
        if not dry_run:
            with open(claude_path, "w", encoding="utf-8") as handle:
                handle.write(CLAUDE_POINTER)
        report.append("create %s (pointer to AGENTS.md)" % claude_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sync_parser = sub.add_parser("sync", help="install/refresh factory skills into harness skill dirs")
    sync_parser.add_argument("--target", action="append", default=None,
                             help="extra/override skill directory (repeatable)")
    sync_parser.add_argument("--copy", action="store_true",
                             help="copy instead of symlink (re-run sync after factory updates)")
    sync_parser.add_argument("--dry-run", action="store_true")

    link_parser = sub.add_parser("link", help="write factory routing into a game repo")
    link_parser.add_argument("--game-repo", required=True)
    link_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "sync":
        targets = args.target if args.target else DEFAULT_SKILL_TARGETS
        lines = sync_skills(FACTORY_ROOT, targets, copy=args.copy, dry_run=args.dry_run)
    else:
        lines = link_game_repo(FACTORY_ROOT, args.game_repo, dry_run=args.dry_run)
    prefix = "[dry-run] " if getattr(args, "dry_run", False) else ""
    for line in lines:
        print(prefix + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
