# arch-tidy — Architecture Cleanup & Hierarchical Documentation

**Date:** 2026-07-09
**Status:** Approved design — ready for implementation planning
**Skill home:** `.claude/skills/arch-tidy/` (project skill; local-only under the repo's `.claude/*` gitignore)
**Trigger:** on-demand (a developer/agent runs it explicitly; never a hook or CI gate)

---

## 1. Overview & goal

`arch-tidy` keeps a codebase's structure honest and self-describing. Its **primary deliverable is selective, hierarchical folder documentation** — a `_folder_context.md` on each *architecturally significant* folder (never one per folder) — that lets a human or agent understand a module without opening its internals. A **secondary phase** proposes file moves that fix modularity violations, so the docs describe a clean tree.

**Design stance (approved):**
- It is a **skill** (LLM judgment) backed by **one deterministic, read-only analysis script**. The script only *analyzes*; the agent following the skill *proposes* moves and *writes* docs.
- **Moves are propose-then-approve**, never silent. The agent executes an approved move (`git mv` + import fixups) using its own tools; the script never mutates files.
- **Documentation is the point; moving is a side service** in support of it.
- It learns **this project's** conventions from existing `_folder_context.md` + layout — it does not impose a generic taxonomy.

## 2. Non-goals (deliberately deferred — YAGNI)

- Auto-applying moves without approval.
- A full multi-language import resolver (the import scan is best-effort; the agent verifies/fixes).
- CI / pre-commit / hook mode.
- Auto-splitting oversized files.
- Documenting every folder.

## 3. Components (each has one responsibility)

```
.claude/skills/arch-tidy/
  SKILL.md                     # the agent's playbook (judgment + orchestration)
  scripts/analyze.py           # deterministic, read-only; emits arch-report.json
  references/context-schema.md  # the _folder_context.md contract
  tests/                       # fixture trees + expected reports
```
Plus a slash command entry point: `/arch-tidy [scope] [--docs-only | --moves-only]`.

## 4. The `_folder_context.md` contract

A machine-readable front-matter block (so the script can reason about placement and freshness) plus human prose.

```markdown
---
module: auth
owns: [routes, services, guards, dtos]   # kinds of things that belong here
boundary: app/auth/index.ts              # public interface (optional)
last_reviewed: <commit-sha or surface-hash>
---
# auth
<1–2 sentence purpose>

## Structure
- services/ — <one line>
- guards/ — <one line>

## Public interface
<what other modules may import>

## Depends on
<key upstream modules>
```

- **`owns`** — what the *placement* check compares a file against.
- **`last_reviewed`** — the **freshness signal**; the doc phase skips a folder whose public surface hash is unchanged, preventing re-doc churn.

## 5. Phase 0 — Analyze (script → `arch-report.json`)

`scripts/analyze.py` is pure, read-only, and language-agnostic where possible. Given a **scope** (explicit paths, or default `git diff --name-only`), it walks the affected directories and their significant ancestors and emits `arch-report.json`:

- **Significance signals** per directory: file count, subdir count, nesting depth, **fan-in / fan-out** (best-effort import scan for JS/TS `import|require` and Python `import|from`), distinct-concern count (heuristic on file kinds/names), is-top-level, already-has-context-file.
- **Placement candidates**: for each changed file, resolve the nearest ancestor `_folder_context.md`; flag files whose inferred kind conflicts with that folder's `owns`. **Candidates + rationale only — never decisions.**
- **Doc gaps**: directories that pass the significance heuristic but have no context file; directories whose `last_reviewed` is stale versus their current surface hash.

Report shape (illustrative):
```json
{
  "scope": ["src/ui/user_model.py", "src/auth/token.py"],
  "dirs": [{ "path": "src/auth", "signals": { "files": 9, "fan_in": 12, "depth": 2, "top_level": true, "has_context": true, "surface_hash": "…", "last_reviewed": "…", "stale": false } }],
  "placement_candidates": [{ "file": "src/ui/user_model.py", "nearest_context": "src/ui/_folder_context.md", "owns": ["components", "hooks"], "inferred_kind": "data-model", "conflict": true, "rationale": "…" }],
  "doc_gaps": [{ "path": "src/payments", "reason": "significant (top-level, fan_in=8) but no _folder_context.md" }]
}
```

## 6. Phase 1 — Structural review (agent, propose-only)

The agent reasons over each `placement_candidate` **against the project's own conventions** (nearby `owns` declarations, existing layout — not a generic rule set):
1. Is it genuinely misplaced, or intentional? (Confidence.)
2. Where does it belong — an existing directory, or a new modular one to create?

It emits a **dry-run** plan: `moves = [{ old, new, reason, confidence }]`, plus the import references that would break (from the script's best-effort graph). **The user approves.** Then the agent executes each move (`git mv`) and fixes the imports with its own tools, and re-runs Phase 0 to confirm zero remaining conflicts. Bounded — it stops when clean; no move-retrigger loop.

## 7. Phase 2 — Hierarchical docs (agent, bottom-up)

Only directories passing the **threshold** get a context file:
- **Qualify if** — a top-level domain module, **or** a clear boundary/interface for internal modules, **or** deep/complex sub-architecture that needs explaining.
- **Omit** — assets, styles, icons, pure-util folders, single-component leaves, and other trivial nodes.

For each qualifying directory:
- **Missing context file** → generate one per the §4 schema.
- **Existing** → update **only if** the change altered the directory's public surface (skip pure-internal edits via `last_reviewed` / surface hash).

Then **walk up** the tree: update an ancestor's `_folder_context.md` **only when a child's one-line summary would actually change** (e.g., a new sub-module appeared or a boundary changed) — avoiding parent-doc churn on every edit.

## 8. Output contract (returned to the calling agent)

- `moves` — proposed (dry-run) or applied `[{ old, new, reason, confidence }]`.
- `import_fixups` — files + import specifiers to update for applied moves.
- `docs_written` — `[{ path, action: "created" | "updated" }]`.
- A short human-readable summary of what changed and why.

## 9. Invocation & modes

- `/arch-tidy` — default scope = working-tree diff; runs Phase 0 → 1 (propose) → 2.
- `/arch-tidy <paths…>` — scope to specific files/dirs.
- `/arch-tidy --docs-only` — skip the move phase (docs only).
- `/arch-tidy --moves-only` — skip doc generation (structural proposals only).

## 10. Safety & correctness guards

- **Read-only script**: `analyze.py` never mutates; all mutations are agent-driven and (for moves) approval-gated.
- **Idempotency**: re-running with no architectural change is a no-op — the doc phase is gated on surface-hash changes; the move phase re-analyzes to a fixed point.
- **Convention-driven**: placement decisions come from the project's `owns` declarations and layout, not a hardcoded taxonomy.
- **Staleness**: `last_reviewed` on each context file marks what surface it was written against.

## 11. Testing

- **Script (unit)**: fixture directory trees → assert `arch-report.json`. Cases: a data-model placed under a UI folder → a `placement_candidate`; an `/icons` leaf → **no** doc gap; a significant `/auth` module lacking a context file → a `doc_gap`; an unchanged folder → `stale: false` (skipped).
- **End-to-end (judgment)**: run the full skill against those fixtures and assert the proposed moves and the set of `_folder_context.md` files created/updated match expectations.
