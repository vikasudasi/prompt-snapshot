# prompt-snapshot

A CLI tool that snapshots your project structure and key file contents into a single markdown document, perfect for feeding into AI agents for context.

## Requirements

1. **Python 3.8+** — no external dependencies (stdlib only)
2. **CLI interface** — `python prompt-snapshot.py [directory] [options]`
3. **Output** — single markdown file written to stdout (or `-o output.md`)

## Features

### File Tree
- Generate a tree view of the directory (like `tree` command)
- Respect `.gitignore` rules (use `pathlib` and manual `.gitignore` parsing)
- Show file sizes and last modified dates

### File Contents
- Include contents of text files (code, markdown, configs, etc.)
- Skip binary files, `.git/`, `node_modules/`, `__pycache__/`, `.venv/`
- Respect `.gitignore`
- Configurable file extensions whitelist (default: .py, .js, .ts, .jsx, .tsx, .md, .json, .yaml, .yml, .toml, .cfg, .ini, .txt, .css, .html, .sh, .bash, .env, .gitignore, Dockerfile, Makefile)
- Configurable max file size (default: 100KB)
- Truncate files over max size with a notice

### Output Format
```
# Project: my-project

## File Tree
```
my-project/
├── src/
│   ├── main.py (2.3 KB, 2024-01-15)
│   └── utils.py (1.1 KB, 2024-01-14)
├── tests/
│   └── test_main.py (0.8 KB, 2024-01-15)
├── README.md (1.5 KB, 2024-01-15)
└── requirements.txt (0.2 KB, 2024-01-13)
```

## File Contents

### src/main.py
\`\`\`python
# file content here
\`\`\`

### src/utils.py
\`\`\`python
# file content here
\`\`\`
```

### Options
- `-o, --output FILE` — write to file instead of stdout
- `-e, --extensions EXT` — comma-separated file extensions to include (e.g. `.py,.js,.md`)
- `-x, --exclude DIR` — additional directories to exclude (can be used multiple times)
- `-s, --max-size KB` — max file size in KB (default: 100)
- `--no-tree` — skip file tree section
- `--no-contents` — skip file contents section
- `-q, --quiet` — suppress warnings
- `-v, --version` — show version

## Files to Create

1. `prompt-snapshot.py` — main CLI script
2. `README.md` — usage docs
3. `setup.py` — optional pip install support

## Implementation Notes

- Use `argparse` for CLI args
- Use `pathlib` for file operations
- Parse `.gitignore` manually (simple line-by-line with glob matching via `fnmatch`)
- Detect binary files by checking for null bytes in first 8KB
- Use `os.stat` for file sizes and dates
- Format dates as `YYYY-MM-DD`
- Format file sizes as human-readable (B, KB, MB)