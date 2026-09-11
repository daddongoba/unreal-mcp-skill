# Contributing

This skill grows from **verified failures**. The most valuable contribution is a
`[VERIFIED]` lesson from a real UE session.

## How lessons get in (Self-Maintenance Protocol)

1. During a session: accumulate draft notes (one line each) — do not edit skill files mid-task.
2. At milestones (session end / ≥5 lessons): batch-commit into the matching capability doc
   or SKILL.md lawbook, update cross-references + version, one backup + one repackage.
3. **Only commit after verification succeeds** — unverified guesses do not belong in the lawbook.

## Confidence tags (mandatory)

| Tag | Meaning |
|---|---|
| `[VERIFIED <date> UE<ver>-<lang>]` | PIE- or user-confirmed. Highest trust. |
| `[DOC]` | Transcribed from official docs/dictionary, not battle-tested. |
| `[UNVERIFIED]` | Theoretically sound, expect failures. Verify before relying. |

When practice contradicts a `[VERIFIED]` entry twice → mark it `[STALE]` and fix it.

## Where things belong

- A **new pitfall/law** → the matching `references/capabilities/<domain>.md` §4, or SKILL.md
  if cross-domain (G-sections, max 12KB budget for the pitfall area).
- A **verified DSL workflow** → `references/templates/<name>.txt` (standard template structure;
  update `templates/README.md` index).
- **Syntax rules** → `references/dsl_syntax.md` (R-numbers).
- **Environment/platform facts** → SKILL.md or `references/platform-macos.md`.

## Pull-request checklist

- [ ] New factual entries carry a confidence tag with date and UE version
- [ ] No machine-local paths (usernames, drive letters tied to a specific machine) —
      parameterize them
- [ ] No secrets/tokens (obviously — but scan anyway)
- [ ] `python3 scripts/refresh_schemas.py` reports **0 DRIFT** (offline cross-check
      between tool_schemas.md and capability docs)
- [ ] Python scripts are stdlib-only and ASCII-safe; PowerShell scripts are PS5.1-compatible
- [ ] SKILL.md version bumped + CHANGELOG.md entry added

## Trademark note

Unreal Engine is a trademark of Epic Games, Inc. Describe engine facts; never imply
endorsement.
