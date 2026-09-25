#!/usr/bin/env sh
# SessionStart hook: injects the i-have-adhd ruleset into every session in this repo.
# Never blocks session start: any failure exits 0.
skill_path="${CLAUDE_PROJECT_DIR:-.}/.claude/skills/i-have-adhd/SKILL.md"
[ -f "$skill_path" ] || exit 0
body=$(awk 'NR==1 && /^---/ {fm=1; next} fm && /^---/ {fm=0; next} !fm' "$skill_path") || exit 0
printf 'ADHD MODE ACTIVE (always-on). The ruleset below applies to every response. "stop adhd mode" turns it off for this session.\n\n%s\n' "$body"
exit 0
