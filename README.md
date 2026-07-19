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
python prompt-snapshot.py [directory] [options]
```

Default directory is `.`.

## Options

- `-o, --output FILE` - write to file instead of stdout
- `-e, --extensions EXT` - comma-separated list of extensions/filenames
- `-x, --exclude DIR_OR_PATH` - additional excludes (repeatable)
- `-s, --max-size KB` - max file size per content block in KB (default: `100`)
- `--no-tree` - omit the file tree section
- `--no-contents` - omit the file contents section
- `-q, --quiet` - suppress warnings
- `-v, --version` - print version and exit

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

## Example

Write a snapshot to a file:

```bash
python prompt-snapshot.py . -o snapshot.md
```
