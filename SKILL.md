---
name: arcane-auditor
description: Workday Extend code review CLI. Use when analyzing PMD, POD, AMD, SMD, script, or orchestration files for quality issues, or when an agent needs machine-readable findings to apply mechanical fixes.
---

# Arcane Auditor — Agent Usage

This CLI analyzes Workday Extend applications and emits structured findings agents can act on. Use the `--agent` preset for everything: it implies `--quiet`, `--format json`, and writes to stdout.

## Quick start

```bash
# Analyze a file, directory, or .zip; emit v2 JSON to stdout.
arcane-auditor review-app <path> --agent

# Discover what rules exist and what each one means.
arcane-auditor list-rules --format json
arcane-auditor describe-rule ScriptVarUsageRule

# Filter to mechanical fixes only.
arcane-auditor review-app <path> --agent --fix-strategy mechanical
```

## v2 JSON output schema

```json
{
  "schema_version": "2.0",
  "summary": {
    "total_files": 0,
    "total_rules": 0,
    "total_findings": 0,
    "findings_by_severity": { "ACTION": 0, "ADVICE": 0 }
  },
  "findings": [
    {
      "rule_id": "ScriptVarUsageRule",
      "severity": "ADVICE",
      "category": "script",
      "fix_strategy": "mechanical",
      "message": "...",
      "location": {
        "file_path": "presentation/foo.pmd",
        "line": 42,
        "column": null,
        "end_line": null,
        "end_column": null,
        "path": "$.body.children[0].onLoad"
      },
      "snippet": "...",
      "suggested_replacement": "let",
      "finding_id": "sha1:abcd1234"
    }
  ]
}
```

### Key fields

- **`fix_strategy`** — How safe this finding is to auto-fix. See decision table below.
- **`location.path`** — JSONPath for JSON-shaped files (PMD/POD/AMD/SMD). Stable across line-drifting edits. `null` for `.script` files and rules without a natural path.
- **`location.line`** — Always set. Use this for `.script` files; use it as a secondary locator for JSON-shaped files when re-reading after edits.
- **`suggested_replacement`** — A single textual token (e.g. `"let"`, `"site.applicationId"`). Drop-in safe at the violation site. Wrapping/punctuation is the agent's responsibility.
- **`snippet`** — A few lines of source around the violation, for context. May be `null` if the analyzer didn't have source content (rare).
- **`finding_id`** — Stable hash of `rule_id|file_path|path|message`. Line is excluded so re-runs after a fix still join.

## `fix_strategy` decision table

| Value | Meaning | Agent behavior |
|---|---|---|
| `mechanical` | Pure textual rewrite, narrow blast radius | Safe to auto-apply |
| `localized` | Narrow rewrite, no cascade | Safe to auto-apply with verification |
| `naming_required` | Agent must invent a meaningful identifier | Attempt; flag for human review |
| `cascading_rename` | Touches multiple files / references | Attempt with caution; verify references |
| `refactor` | Multi-step rewrite | Attempt; require human approval |
| `design_decision` | Requires human judgment | Surface as comment; do not auto-fix |

## Loop strategy

Re-running the analyzer after each fix is cheap and sidesteps line-drift bookkeeping.

```
loop:
  result = arcane-auditor review-app <path> --agent
  fixable = [f for f in result.findings if f.fix_strategy in {mechanical, localized}]
  if not fixable: break
  pick one finding
  apply fix (prefer location.path; fall back to location.line)
  goto top
```

## JSONPath vs. line guidance

- **JSON-shaped files (PMD, POD, AMD, SMD):** `location.path` is the most stable locator across line-drifting edits. Use it to locate the node, then read/rewrite from there.
- **Script bodies inside JSON (`<% %>`):** `location.path` finds the *containing field*. Line numbers within the script body still drift after edits — re-read the field after each fix.
- **`.script` files (raw):** `location.path` is `null`. Use `location.line`.

## Filtering

| Flag | Effect |
|---|---|
| `--rules R1,R2` | Run only these rules (faster) |
| `--exclude-rules R3` | Skip these rules |
| `--severity ACTION` | Keep only ACTION-severity findings |
| `--fix-strategy mechanical,localized` | Keep only findings with these strategies |
| `--files <glob>` | fnmatch glob limiting which input files are parsed |

Unknown rule IDs or invalid filter values exit with code 2.

## Exit codes

- `0` — Clean run, or only ADVICE issues (unless `--fail-on-advice`)
- `1` — ACTION issues found (or ADVICE with `--fail-on-advice`)
- `2` — Usage error (bad flag, unknown rule, no input files)
- `3` — Runtime error (parse failure, analyzer crash)
