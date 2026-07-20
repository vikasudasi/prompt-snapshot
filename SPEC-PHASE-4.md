# Phase 4: Power-User and Monorepo Workflows

**Status:** Planned  
**Depends on:** Phase 1–3

## Goal

Support advanced workflows: snapshot only what changed, split output for monorepos, and target specific token budgets for AI tools.

## Features

### 1. Git Diff Mode

Snapshot only files changed relative to a git ref:

```bash
--git-diff                  # changed files vs HEAD (staged + unstaged + untracked)
--git-diff main             # vs branch or ref
--git-diff HEAD~5           # vs 5 commits ago
--git-diff --cached         # staged only
```

**Behavior:**
- Run `git diff --name-only` and `git ls-files --others --exclude-standard` to collect paths
- Intersect with normal include/exclude rules
- Tree section shows only changed files (or `--no-tree` with contents only)
- Requires git repo; error with clear message if not in one

Implementation: subprocess call to `git` (no libgit2 dependency). Paths resolved relative to repo root.

### 2. Split Output by Directory

For monorepos, produce one markdown file per top-level directory:

```bash
--split-by top-level        # one file per immediate child dir
--split-by package          # detect packages via package.json, pyproject.toml, etc.
-o snapshots/               # output directory (required with --split-by)
```

**Output:**

```
snapshots/
├── src.md
├── pkg-api.md
├── pkg-web.md
└── README.md
```

Each file is a self-contained snapshot with its own tree and contents. Global limits (`--max-files`, `--max-output-mb`) apply per output file.

### 3. Token Estimator

Estimate token count for AI context budgeting:

```bash
--max-tokens 128000         # stop when estimated tokens exceed limit
--show-tokens               # print token estimate to stderr after completion
```

**Estimation heuristic (no external tokenizer):**
- Default: `len(text) / 4` (rough chars-to-tokens ratio)
- Optional: `--tokenizer MODEL` for future plugin support (non-goal for initial impl)

Summary header (from Phase 2) includes estimated token count:

```markdown
> 142 files included · ~48,200 tokens (estimated)
```

### 4. Nested Code Fence Escaping

Markdown files in snapshots can contain ` ``` ` blocks that break the outer fence.

**Fix:** Detect nested fences and use longer outer fences:

````markdown
### docs/guide.md
````markdown
Here's an example:

```python
print("hello")
```
````
````

Implementation: scan content for max consecutive backtick run, use `max + 1` backticks for wrapping fence.

### 5. Optional Line Numbers

```bash
--line-numbers    # prefix each line with its line number in code blocks
```

Useful for code review context. Format: `   1 | code here`

## CLI Additions

| Option | Description |
|--------|-------------|
| `--git-diff [REF]` | Include only changed files vs ref (default: working tree) |
| `--git-diff-cached` | Staged changes only |
| `--split-by MODE` | Split output (`top-level`, `package`) |
| `--max-tokens N` | Stop when estimated tokens exceed N |
| `--show-tokens` | Print token estimate to stderr |
| `--line-numbers` | Add line numbers to code blocks |

## Tests

- Git diff mode returns only changed files (mock subprocess or temp git repo)
- Split output creates multiple files in output directory
- Token estimator stops before exceeding `--max-tokens`
- Nested fence escaping handles markdown files with code blocks
- Line numbers format correctly

## Non-Goals (Phase 4)

- External tokenizer libraries (tiktoken, etc.) — heuristic only
- libgit2 / dulwich — use git subprocess
- Watch mode / incremental updates
- Upload directly to AI APIs

## Future Considerations (Post-Phase 4)

- Progress bar for large repos (`--progress`)
- `.prompt-snapshotignore` as a dedicated ignore file
- Plugin system for custom formatters (JSON, XML)
- Integration with Cursor / Claude context APIs
