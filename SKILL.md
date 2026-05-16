---

## name: arcane-auditor
description: Workday Extend code review CLI. Use when analyzing PMD, POD, AMD, SMD, script, or orchestration files for quality issues, or when an agent needs machine-readable findings to triage and apply suggested fixes.

# Arcane Auditor — Agent Usage

This CLI analyzes Workday Extend applications and emits structured findings agents can act on. Use the `--agent` preset for everything: it implies `--quiet`, `--format json`, and writes to stdout.

**No telemetry. No network. No bundled LLM. No auto-fix.** The tool surfaces findings (and, where deterministic, a suggested replacement string) — an agent or the user decides whether to splice it in. All analysis runs locally.

## Binary name

The shipped binary is **`ArcaneAuditorCLI`** (`.exe` on Windows). Source/dev installs may expose the same binary as `arcane-auditor` via the `pyproject.toml` console script — substitute as needed.

If the command isn't on PATH, ask the user once for the absolute path and use it for the rest of the session. Don't attempt to install, move, or PATH-modify on the user's behalf.

## Trigger phrases

Users typically ask for an audit with phrases like:

- "audit this app" / "run arcane auditor on `<path>`"
- "check this Extend app for code issues"
- "what does arcane auditor say about `<file>`"

On any of these, invoke `ArcaneAuditorCLI review-app <path> --agent` and triage findings as described below.

## Quick start

```bash
# Analyze a file, directory, or .zip; emit JSON to stdout.
ArcaneAuditorCLI review-app <path> --agent

# Discover what rules exist and what each one means.
ArcaneAuditorCLI list-rules --format json
ArcaneAuditorCLI describe-rule ScriptVarUsageRule

# Filter to actionable findings only (those carrying a suggested_replacement).
ArcaneAuditorCLI review-app <path> --agent --fix-strategy actionable
```

`--agent` is mutually exclusive with `--ci` and rejects non-JSON `--format` (both exit code 2). Output ordering is deterministic — findings are sorted by `(file_path, line, rule_id, message)`, so re-runs diff cleanly.

## JSON output schema

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
      "fix_strategy": "actionable",
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
      "target_text": "var",
      "replacement_context": "substring",
      "finding_id": "sha1:<hash — yours will differ>"
    }
  ]
}
```

### Key fields

- `**fix_strategy**` — How an agent should handle this finding. See decision table below.
- `**location.path**` — JSONPath for JSON-shaped files (PMD/POD/AMD/SMD). Stable across line-drifting edits. `null` for `.script` files and rules without a natural path.
- `**location.line**` — Always set. Use this for `.script` files; use it as a secondary locator for JSON-shaped files when re-reading after edits.
- `**location.column` / `end_line` / `end_column**` — Currently emitted as `null` across all rules; reserved for future use. Don't rely on them.
- `**suggested_replacement**` — The new text that goes in place of `target_text` (when `target_text` is set), or the new value of the field (when `target_text` is `null` — `full_field` context). It is the *post-edit substring*, not the bare new value — rules may include surrounding context (e.g. `"visible": true`, not just `true`) to make the swap unambiguous. May itself be `null` on `actionable` findings whose fix is whole-document (e.g., reordering keys); in that case the `message` carries the spec.
- `**target_text**` — Exact original substring that `suggested_replacement` swaps in for. When present, the agent should locate this string within the field at `location.path` and replace it — do NOT replace the whole field. May be `null` when the rule emits a full-field/whole-document replacement.
- `**replacement_context**` — How to apply `suggested_replacement`. See table below. May be `null` on older/un-enriched rules; treat `null` as `full_field` only when `target_text` is also `null`, otherwise default to `substring`.
- `**snippet**` — A few lines of source around the violation, for context. May be `null` if the analyzer didn't have source content (rare).
- `**finding_id**` — Stable hash of `rule_id|file_path|path|message`. Line is excluded so re-runs after a fix still join on the same identifier. The example value above is illustrative; real runs produce different hashes.

## `fix_strategy` decision table


| Value          | Meaning                                                                                                              | Agent behavior                                                                          |
| -------------- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `actionable`   | Finding carries a deterministic fix; a `suggested_replacement` may be present (or, rarely, the spec is in `message`) | **Apply the fix directly. Do not ask the user first.** Report what was changed afterward. |
| `human_review` | Resolution requires human judgment, multi-step rewrites, naming, cross-file work, or workflow that crosses systems   | Surface for human review and ask before changing anything; do not auto-resolve.         |

### `replacement_context` decision table


| Value           | How to apply                                                                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `substring`     | Read the field at `location.path`, replace the literal `target_text` with `suggested_replacement`, write the field back. **Never** overwrite the whole field.         |
| `full_field`    | Replace the entire value at `location.path` with `suggested_replacement`.                                                                                             |
| `array_splice`  | `suggested_replacement` is a comma-separated set of array elements; splice them into the existing array at `location.path` (preserve existing elements).              |
| `array_remove`  | `target_text` is one element's literal text within the array at `location.path`; remove that element, dropping its surrounding comma. `suggested_replacement` is empty. Preserve other elements. |
| `field_insert`  | `suggested_replacement` is a `"key": value` pair; insert it into the object at `location.path`.                                                                       |


**Common foot-gun:** for script bodies embedded in JSON (`<% ... %>`), `location.path` points at the *containing field*, and the rule's `target_text` is a fragment of the script — e.g., a `'a' + b` concat inside `<% const a = 'x'; return 'a' + b; %>`. Replacing the whole field deletes the surrounding script (variable declarations, control flow). Always honor `target_text` + `replacement_context` when they are present.

`fix_strategy` is the user's standing instruction to the agent, not a suggestion to re-litigate. The rule author picks a sensible default, and users can override per rule in tool config — so by the time a finding reaches the agent with `actionable`, the user has already consented to the agent applying it. Asking again defeats the purpose. If you are unsure whether a specific fix is safe, the right response is to flag the rule's classification for review, not to prompt on every individual finding.

About 12 of 48 rules ship with `actionable` as the default; the rest default to `human_review`. Trust the strategy on the finding.

Before triaging a `human_review` finding, call `ArcaneAuditorCLI describe-rule <RuleId>` — it returns the full rule metadata including `why`, `catches`, `examples`, and `recommendation` to help the agent (or user) reason about the right response.

## Loop strategy

Re-running the analyzer after each fix is cheap and sidesteps line-drift bookkeeping. Apply `actionable` fixes without prompting — the user has already opted in via the rule's strategy. Summarize what changed at the end of the loop, not before each edit.

```
loop:
  result = ArcaneAuditorCLI review-app <path> --agent
  fixable = [f for f in result.findings if f.fix_strategy == "actionable" and f.suggested_replacement]
  if not fixable: break
  pick one finding
  read the field at f.location.path (or the line for .script files)
  apply fix per f.replacement_context (see table above):
    - substring:    new_field = field.replace(f.target_text, f.suggested_replacement)
    - full_field:   new_field = f.suggested_replacement
    - array_splice / array_remove / field_insert: splice/remove/insert per table
  write the field back
  verify post-fix (see below)
  goto top
# then surface remaining human_review findings to the user
```

### Post-fix verification (required for `substring`, `array_splice`, and `array_remove`)

After applying a fragment fix, **re-read the surrounding context** before continuing the loop. A clean re-run of the auditor proves the *targeted* rule is satisfied, but rules don't model cross-cutting effects of the edit. Specifically:

- **Script bodies (`<% %>` in PMD/POD):** confirm the script still parses by eye — every identifier referenced in `suggested_replacement` (e.g., `{{name}}` in a template literal) must resolve to a `var`/`let`/`const` or parameter still present in scope. If the fix removed the last use of a previously-declared variable, that variable is now unused (a separate rule will catch it on the next pass — that's expected).
- **JSON splices/inserts:** confirm the resulting field is still valid JSON (no trailing commas, balanced braces).
- **`.script` files:** re-read the line and ±2 lines around it.

If the re-read looks wrong, **revert the edit** and reclassify the finding as `human_review` for the user. Trusting "0 findings" alone is the foot-gun that motivates `target_text` in the first place.

Re-reading the target field after each fix matters especially for script bodies embedded in PMD/POD JSON — see the next section.

## JSONPath vs. line guidance

- **JSON-shaped files (PMD, POD, AMD, SMD):** `location.path` is the most stable locator across line-drifting edits. Use it to locate the node, then read/rewrite from there.
- **Script bodies inside JSON (`<% %>`):** `location.path` finds the *containing field*. Line numbers within the script body still drift after edits — re-read the field after each fix.
- `**.script` files (raw):** `location.path` is `null`. Use `location.line`.

## Filtering


| Flag                        | Effect                                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| `--rules R1,R2`             | Run only these rules (faster)                                                                         |
| `--exclude-rules R3`        | Skip these rules                                                                                      |
| `--severity ACTION`         | Keep only ACTION-severity findings                                                                    |
| `--fix-strategy actionable` | Keep only findings with this strategy (or `human_review`)                                             |
| `--files <glob,glob>`       | Comma-separated fnmatch globs limiting which input files are parsed; file kept if ANY pattern matches |
| `--fail-on-advice`          | Exit `1` even when only ADVICE issues are present                                                     |


Unknown rule IDs or invalid filter values exit with code 2.

## Exit codes

- `0` — Clean run, or only ADVICE issues (unless `--fail-on-advice`)
- `1` — ACTION issues found (or ADVICE with `--fail-on-advice`)
- `2` — Usage error (bad flag, unknown rule, no input files, `--agent` combined with `--ci` or non-JSON `--format`)
- `3` — Runtime error (parse failure, analyzer crash)

