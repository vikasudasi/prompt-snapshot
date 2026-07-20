# Phase 2: AI-Focused Improvements

**Status:** Planned  
**Depends on:** Phase 1 (streaming, global limits)

## Goal

Make snapshots useful within real AI context windows by prioritizing the most valuable files and surfacing metadata about what was included and what was skipped.

## Features

### 1. Summary Header

Add a metadata block immediately after the project title:

```markdown
# Project: my-app

> 12,400 files scanned · 142 included · 2.1 MB output · 23 skipped (size) · 705 skipped (extension)

## File Tree
...
```

Fields:
- `files_scanned` — total non-excluded files discovered during walk
- `files_included` — files written to the contents section
- `output_bytes` — final output size (human-readable)
- `files_skipped_*` — breakdown by reason (extension, binary, size, limit)

Implementation: extend `SnapshotStats` (already present from Phase 1) and write the header before the tree section.

### 2. Smart File Prioritization

When `--max-files` or `--max-output-mb` limits apply, include the most useful files first instead of filesystem order.

**Default priority tiers (highest first):**

| Tier | Patterns | Rationale |
|------|----------|-----------|
| 1 | `README*`, `SPEC*`, `CONTRIBUTING*`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` | Project overview and dependencies |
| 2 | `**/main.*`, `**/index.*`, `**/app.*`, `**/cli.*` | Entry points |
| 3 | `src/**`, `lib/**`, `pkg/**` | Core source code |
| 4 | `**/*.{py,ts,js,go,rs}` | General source files |
| 5 | `tests/**`, `**/*_test.*`, `**/*.test.*` | Tests (lower priority) |
| 6 | Everything else matching extensions | Remaining files |

**CLI:**

```bash
--priority PATTERN    # Add a custom priority glob (repeatable, earlier = higher)
--no-default-priority # Disable built-in priority tiers
```

Implementation: after `walk_project()`, sort `content_files` by computed priority score before writing contents.

### 3. Presets

Convenience flags that set multiple options at once:

```bash
--preset ai-context
```

Equivalent to:

```bash
-e .py,.ts,.js,.md,.json,.yaml,.toml \
-x tests,fixtures,__mocks__,node_modules \
-s 30 \
--max-files 150 \
--max-output-mb 2
```

```bash
--preset overview
```

Equivalent to:

```bash
--no-contents
```

```bash
--preset minimal
```

Equivalent to:

```bash
--no-contents --tree-depth 2
```

(Requires `--tree-depth` from Phase 2 or deferred to Phase 3.)

### 4. Tree Depth Limit

```bash
--tree-depth N    # Only show N levels deep in the file tree (0 = unlimited)
```

Useful for huge repos where even the tree section is too large.

## CLI Additions

| Option | Description |
|--------|-------------|
| `--preset NAME` | Apply a named preset (`ai-context`, `overview`, `minimal`) |
| `--priority PATTERN` | Custom priority glob (repeatable) |
| `--no-default-priority` | Disable built-in priority tiers |
| `--tree-depth N` | Limit file tree depth |

## Tests

- Priority sorting: README included before `tests/` files when `--max-files 1`
- Preset `ai-context` sets expected defaults
- Summary header contains correct counts
- Tree depth limits tree lines but not content file collection

## Non-Goals (Phase 2)

- Token counting (Phase 4)
- Config file (Phase 3)
- Git diff mode (Phase 4)
