# Phase 3: Filtering and Configuration

**Status:** Planned  
**Depends on:** Phase 1 (streaming, global limits), Phase 2 (prioritization) recommended

## Goal

Give users fine-grained control over what gets included without long CLI invocations, and improve gitignore accuracy for real-world repos.

## Features

### 1. Include Globs

Extensions are coarse. Add glob-based include/exclude patterns:

```bash
--include "src/**/*.py"           # repeatable
--include "**/README.md"
--exclude-glob "**/*_test.go"     # repeatable, applied after includes
```

**Resolution order:**
1. File must match at least one `--include` pattern (if any `--include` given)
2. File must match allowed extensions (if no `--include` given, extensions apply as today)
3. File must not match any `--exclude-glob` pattern
4. File must not be excluded by `-x`, default dirs, or gitignore

Implementation: use `fnmatch` or `pathlib.PurePath.match()` for glob matching. When `--include` patterns are provided, they replace (not supplement) the extension whitelist unless `--extensions` is also given (both must match).

### 2. Config File

Support a project-level config file to avoid repeating flags:

**Search order:**
1. `.prompt-snapshot.yaml`
2. `.prompt-snapshot.yml`
3. `prompt-snapshot.yaml` in project root

**Example `.prompt-snapshot.yaml`:**

```yaml
extensions:
  - .py
  - .ts
  - .md
exclude:
  - vendor
  - dist
  - node_modules
exclude_glob:
  - "**/*_test.py"
  - "**/fixtures/**"
include:
  - "src/**"
  - "README.md"
max_size_kb: 50
max_files: 200
max_output_mb: 2
priority:
  - README.md
  - src/**
preset: ai-context
tree_depth: 3
no_tree: false
no_contents: false
```

**CLI override:** All CLI flags override config file values. Use `--no-config` to ignore config files entirely.

**Parsing:** Use stdlib only. Parse YAML with a minimal hand-rolled parser for the subset needed, or require JSON config (`.prompt-snapshot.json`) to stay dependency-free. Recommended: support JSON natively and YAML via a simple subset parser (key: value, lists with `-`).

### 3. Nested `.gitignore` Support

Current behavior: only reads root `.gitignore`.

**Improved behavior:**
- During walk, load `.gitignore` from each entered directory
- Merge rules with directory-scoped applicability (git-style)
- Also read `.git/info/exclude` if `.git` exists

Implementation:
- Replace flat `List[GitignoreRule]` with `Dict[Path, List[GitignoreRule]]` keyed by directory
- When checking `is_excluded`, collect rules from root to current directory
- Cache loaded rules per directory to avoid re-reading

### 4. Compact Tree Mode

```bash
--compact-tree    # Show directories only, no individual files in tree
```

Reduces tree output size for monorepos while still including file contents.

## CLI Additions

| Option | Description |
|--------|-------------|
| `--include GLOB` | Include files matching glob (repeatable) |
| `--exclude-glob GLOB` | Exclude files matching glob (repeatable) |
| `--config FILE` | Explicit config file path |
| `--no-config` | Ignore config files |
| `--compact-tree` | Directories only in tree section |

## Tests

- Include glob `src/**/*.py` excludes top-level scripts
- Config file values applied; CLI flags override
- Nested gitignore: `subdir/.gitignore` excludes files only under `subdir/`
- Compact tree omits file entries but contents section unchanged

## Non-Goals (Phase 3)

- Token estimation (Phase 4)
- Split output by directory (Phase 4)
- External YAML library dependency
