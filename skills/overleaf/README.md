# Overleaf skill for Claude Code

Clone, edit, commit, and push Overleaf LaTeX projects via Overleaf's git bridge — all inside a Claude Code session.

## Install

```bash
mkdir -p ~/.claude/skills/overleaf
curl -fsSL https://raw.githubusercontent.com/guylaban/my-stuff/claude/add-conference-rankings-OnzzT/skills/overleaf/SKILL.md \
  -o ~/.claude/skills/overleaf/SKILL.md
```

Then restart Claude Code and invoke with `/overleaf` or just ask it to edit an Overleaf project.

## Requirements

- An Overleaf plan that includes **Git integration** (paid plans).
- A **Git authentication token** from https://www.overleaf.com/user/settings → "Git Integration".
- The project's **24-char project ID** (from `overleaf.com/project/<id>` — share links won't work).

See `SKILL.md` for full details.
