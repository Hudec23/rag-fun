#!/bin/sh
# Wire the autospec kit (in .autospec/kit/) into this project. Safe to run again: it only creates
# what is missing and never overwrites your files. Run from the project root:
#   sh .autospec/kit/init.sh
set -eu

KIT=.autospec/kit
[ -f "$KIT/PLANNER.md" ] || { echo "run from the project root; expected the kit in $KIT/" >&2; exit 1; }
[ "$(git rev-parse --show-toplevel 2>/dev/null)" = "$(pwd -P)" ] || { echo "run from the git repo root" >&2; exit 1; }

say() { printf '  %s\n' "$*"; }

# Planner skills for Claude Code: symlinks, so kit updates apply without re-running init.
mkdir -p .claude/skills
for dir in "$KIT"/skills/autospec-*; do
  name=$(basename "$dir")
  if [ ! -e ".claude/skills/$name" ]; then
    ln -s "../../$KIT/skills/$name" ".claude/skills/$name"
    say "linked .claude/skills/$name"
  fi
done

# CLAUDE.md: Claude Code imports the planner instructions from the kit.
if [ ! -f CLAUDE.md ]; then
  printf '@%s/PLANNER.md\n\n# Project notes\n' "$KIT" > CLAUDE.md
  say "created CLAUDE.md"
elif ! grep -q "@$KIT/PLANNER.md" CLAUDE.md; then
  printf '\n@%s/PLANNER.md\n' "$KIT" >> CLAUDE.md
  say "added @$KIT/PLANNER.md to CLAUDE.md"
fi

# AGENTS.md must exist: without it opencode falls back to CLAUDE.md (the planner's instructions).
if [ ! -f AGENTS.md ]; then
  cp "$KIT/templates/AGENTS.md" AGENTS.md
  say "created AGENTS.md (the planner fills # Commands)"
fi

# opencode.json: executor rules, hidden planner skills, rescue subagent.
if [ ! -f opencode.json ]; then
  cp "$KIT/templates/opencode.json" opencode.json
  say "created opencode.json"
elif ! grep -q "$KIT/EXECUTOR.md" opencode.json; then
  say "WARNING: opencode.json exists; merge $KIT/templates/opencode.json into it by hand"
fi

# Runner files that must never be committed.
touch .gitignore
for line in .autospec/runs/ .autospec/BLOCKED_REASON .autospec/STOP; do
  grep -qxF "$line" .gitignore || { echo "$line" >> .gitignore; say "gitignored $line"; }
done

echo "autospec ready. Next: open Claude Code here and run /autospec-system"
