# prompt-snapshot

`prompt-snapshot` creates a single markdown document with:
- a project file tree
- selected file contents

This is useful when sharing repository context with AI assistants.

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)

## Usage

Run directly:

```bash
python3 prompt-snapshot.py [directory] [options]
```

Default directory is `.`.

## Options

| Option | Description |
|--------|-------------|
| `-o, --output FILE` | Write to file instead of stdout |
| `-e, --extensions EXT` | Comma-separated list of extensions/filenames |
| `-x, --exclude DIR_OR_PATH` | Additional excludes (repeatable) |
| `-s, --max-size KB` | Max file size per content block in KB (default: `100`) |
| `--max-files N` | Max number of files in the contents section |
| `--max-output-mb MB` | Max total output size in megabytes |
| `--no-tree` | Omit the file tree section |
| `--no-contents` | Omit the file contents section |
| `-q, --quiet` | Suppress warnings |
| `-v, --version` | Print version and exit |

## Defaults

### Included extensions/filenames

`.py, .js, .ts, .jsx, .tsx, .md, .json, .yaml, .yml, .toml, .cfg, .ini, .txt, .css, .html, .sh, .bash, .env, .gitignore, Dockerfile, Makefile`

### Always-excluded directories

`.git`, `node_modules`, `__pycache__`, `.venv`

## Notes

- `.gitignore` is parsed and respected
- Binary files are skipped (null-byte detection on first 8KB)
- Oversized files are truncated with a note
- Dates are formatted `YYYY-MM-DD`
- Sizes are formatted as `B`, `KB`, `MB`
- Output is streamed directly to the destination (low memory footprint)
- The project tree is walked once (not twice)
- When `--max-files` or `--max-output-mb` limits are hit, a truncation footer is appended

## Examples

Write a snapshot to a file:

```bash
python3 prompt-snapshot.py . -o snapshot.md
```

Bounded snapshot for large repos (AI context):

```bash
python3 prompt-snapshot.py . \
  -e .py,.ts,.md \
  -x tests,fixtures \
  -s 30 \
  --max-files 150 \
  --max-output-mb 2 \
  -o context.md
```

Tree only (fast overview):

```bash
python3 prompt-snapshot.py . --no-contents -o tree.md
```

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | Done | Streaming output, single walk, global limits (`--max-files`, `--max-output-mb`) |
| **Phase 2** | Planned | Smart prioritization, summary header, AI presets — see [SPEC-PHASE-2.md](SPEC-PHASE-2.md) |
| **Phase 3** | Planned | Include globs, config file, nested gitignore — see [SPEC-PHASE-3.md](SPEC-PHASE-3.md) |
| **Phase 4** | Planned | Git diff mode, split output, token estimator — see [SPEC-PHASE-4.md](SPEC-PHASE-4.md) |

See [SPEC.md](SPEC.md) for the original design spec.
