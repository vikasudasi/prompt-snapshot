#!/usr/bin/env python3
"""Generate a markdown snapshot of a project tree and key file contents."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

VERSION = "0.1.0"
DEFAULT_MAX_SIZE_KB = 100
DEFAULT_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".txt",
    ".css",
    ".html",
    ".sh",
    ".bash",
    ".env",
    ".gitignore",
    "Dockerfile",
    "Makefile",
)
DEFAULT_EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "tsx",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".cfg": "ini",
    ".ini": "ini",
    ".txt": "text",
    ".css": "css",
    ".html": "html",
    ".sh": "bash",
    ".bash": "bash",
}


@dataclass(frozen=True)
class GitignoreRule:
    pattern: str
    negate: bool
    dir_only: bool
    anchored: bool


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Snapshot a project tree and file contents into markdown."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Target directory to snapshot (default: current directory).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write markdown output to this file instead of stdout.",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        help="Comma-separated list of allowed extensions and/or filenames.",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        help="Additional directory names or relative paths to exclude.",
    )
    parser.add_argument(
        "-s",
        "--max-size",
        type=int,
        default=DEFAULT_MAX_SIZE_KB,
        metavar="KB",
        help=f"Maximum file size in KB for content inclusion (default: {DEFAULT_MAX_SIZE_KB}).",
    )
    parser.add_argument(
        "--no-tree",
        action="store_true",
        help="Skip the file tree section.",
    )
    parser.add_argument(
        "--no-contents",
        action="store_true",
        help="Skip the file contents section.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress warnings.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    args = parser.parse_args(argv)
    if args.max_size < 0:
        parser.error("--max-size must be >= 0")
    return args


def warn(msg: str, quiet: bool) -> None:
    if not quiet:
        print(f"warning: {msg}", file=sys.stderr)


def parse_extensions(value: str | None) -> Set[str]:
    if not value:
        return set(DEFAULT_EXTENSIONS)
    items = [part.strip() for part in value.split(",")]
    return {item for item in items if item}


def load_gitignore_rules(root: Path) -> List[GitignoreRule]:
    gitignore_path = root / ".gitignore"
    if not gitignore_path.is_file():
        return []

    rules: List[GitignoreRule] = []
    try:
        raw_lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in raw_lines:
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue

        negate = raw.startswith("!")
        pattern = raw[1:] if negate else raw
        if not pattern:
            continue

        dir_only = pattern.endswith("/")
        if dir_only:
            pattern = pattern.rstrip("/")
            if not pattern:
                continue

        anchored = pattern.startswith("/")
        if anchored:
            pattern = pattern.lstrip("/")
        rules.append(
            GitignoreRule(
                pattern=pattern,
                negate=negate,
                dir_only=dir_only,
                anchored=anchored,
            )
        )
    return rules


def _match_unanchored(pattern: str, rel_path: str) -> bool:
    if fnmatch.fnmatch(rel_path, pattern):
        return True
    parts = rel_path.split("/")
    for idx in range(len(parts)):
        candidate = "/".join(parts[idx:])
        if fnmatch.fnmatch(candidate, pattern):
            return True
    if fnmatch.fnmatch(parts[-1], pattern):
        return True
    return False


def rule_matches(rule: GitignoreRule, rel_path: Path, is_dir: bool) -> bool:
    if rule.dir_only and not is_dir:
        return False

    rel_text = rel_path.as_posix()
    if rel_text in ("", "."):
        return False

    if rule.anchored:
        return fnmatch.fnmatch(rel_text, rule.pattern)
    return _match_unanchored(rule.pattern, rel_text)


def gitignore_ignored(rel_path: Path, is_dir: bool, rules: Sequence[GitignoreRule]) -> bool:
    ignored = False
    for rule in rules:
        if rule_matches(rule, rel_path, is_dir):
            ignored = not rule.negate
    return ignored


def normalize_path_token(token: str) -> str:
    return Path(token).as_posix().strip("/")


def is_excluded(
    abs_path: Path,
    root: Path,
    is_dir: bool,
    excluded_dirs: Set[str],
    excluded_paths: Set[str],
    gitignore_rules: Sequence[GitignoreRule],
) -> bool:
    try:
        rel = abs_path.relative_to(root)
    except ValueError:
        return True

    rel_text = rel.as_posix()
    rel_key = normalize_path_token(rel_text)

    if is_dir and abs_path.name in excluded_dirs:
        return True

    if rel_key and rel_key in excluded_paths:
        return True

    if rel_key:
        for part in rel.parts:
            if part in excluded_paths:
                return True

    if gitignore_ignored(rel, is_dir=is_dir, rules=gitignore_rules):
        return True

    return False


def format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def format_date(timestamp: float) -> str:
    return dt.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


def should_include_by_extension(path: Path, allowed: Set[str]) -> bool:
    if path.name in allowed:
        return True
    if path.suffix in allowed:
        return True
    return False


def markdown_language(path: Path) -> str:
    if path.name in ("Dockerfile", "Makefile"):
        return "text"
    return LANGUAGE_BY_SUFFIX.get(path.suffix, "text")


def list_entries(
    directory: Path,
    root: Path,
    excluded_dirs: Set[str],
    excluded_paths: Set[str],
    gitignore_rules: Sequence[GitignoreRule],
) -> List[Path]:
    children: List[Path] = []
    try:
        for child in directory.iterdir():
            is_dir = child.is_dir()
            if is_excluded(
                child,
                root=root,
                is_dir=is_dir,
                excluded_dirs=excluded_dirs,
                excluded_paths=excluded_paths,
                gitignore_rules=gitignore_rules,
            ):
                continue
            children.append(child)
    except OSError:
        return []
    children.sort(key=lambda p: (not p.is_dir(), p.name.lower()))
    return children


def build_tree_lines(
    root: Path,
    excluded_dirs: Set[str],
    excluded_paths: Set[str],
    gitignore_rules: Sequence[GitignoreRule],
) -> List[str]:
    lines = [f"{root.name}/"]

    def visit(directory: Path, prefix: str) -> None:
        entries = list_entries(
            directory,
            root=root,
            excluded_dirs=excluded_dirs,
            excluded_paths=excluded_paths,
            gitignore_rules=gitignore_rules,
        )
        for idx, child in enumerate(entries):
            is_last = idx == len(entries) - 1
            branch = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "
            if child.is_dir():
                lines.append(f"{prefix}{branch}{child.name}/")
                visit(child, prefix + child_prefix)
                continue

            try:
                stat = child.stat()
                meta = f"({format_size(stat.st_size)}, {format_date(stat.st_mtime)})"
            except OSError:
                meta = "(unreadable)"
            lines.append(f"{prefix}{branch}{child.name} {meta}")

    visit(root, "")
    return lines


def iter_candidate_files(
    root: Path,
    excluded_dirs: Set[str],
    excluded_paths: Set[str],
    gitignore_rules: Sequence[GitignoreRule],
) -> Iterable[Path]:
    for current_root, dirs, files in os.walk(root, topdown=True):
        current_path = Path(current_root)
        kept_dirs: List[str] = []
        for dirname in sorted(dirs):
            abs_dir = current_path / dirname
            if is_excluded(
                abs_dir,
                root=root,
                is_dir=True,
                excluded_dirs=excluded_dirs,
                excluded_paths=excluded_paths,
                gitignore_rules=gitignore_rules,
            ):
                continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in sorted(files):
            abs_file = current_path / filename
            if is_excluded(
                abs_file,
                root=root,
                is_dir=False,
                excluded_dirs=excluded_dirs,
                excluded_paths=excluded_paths,
                gitignore_rules=gitignore_rules,
            ):
                continue
            yield abs_file


def read_file_content(path: Path, max_bytes: int, quiet: bool) -> Tuple[str, bool]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        warn(f"could not stat {path}: {exc}", quiet)
        return "", False

    truncated = size > max_bytes
    to_read = max_bytes if truncated else size
    try:
        with path.open("rb") as fh:
            data = fh.read(to_read)
    except OSError as exc:
        warn(f"could not read {path}: {exc}", quiet)
        return "", False

    text = data.decode("utf-8", errors="replace")
    if truncated:
        text += (
            "\n\n[... truncated ...]\n"
            f"[File exceeds max size ({format_size(size)} > {format_size(max_bytes)})]"
        )
    return text, True


def build_snapshot(
    root: Path,
    allowed_extensions: Set[str],
    excluded_dirs: Set[str],
    excluded_paths: Set[str],
    gitignore_rules: Sequence[GitignoreRule],
    max_size_kb: int,
    include_tree: bool,
    include_contents: bool,
    quiet: bool,
) -> str:
    parts: List[str] = [f"# Project: {root.name}"]

    if include_tree:
        tree_lines = build_tree_lines(
            root=root,
            excluded_dirs=excluded_dirs,
            excluded_paths=excluded_paths,
            gitignore_rules=gitignore_rules,
        )
        parts.extend(["", "## File Tree", "```", *tree_lines, "```"])

    if include_contents:
        parts.extend(["", "## File Contents"])
        max_bytes = max_size_kb * 1024
        for path in iter_candidate_files(
            root=root,
            excluded_dirs=excluded_dirs,
            excluded_paths=excluded_paths,
            gitignore_rules=gitignore_rules,
        ):
            if not should_include_by_extension(path, allowed_extensions):
                continue
            if is_binary_file(path):
                continue
            content, ok = read_file_content(path, max_bytes=max_bytes, quiet=quiet)
            if not ok:
                continue
            rel = path.relative_to(root).as_posix()
            lang = markdown_language(path)
            parts.extend(["", f"### {rel}", f"```{lang}", content, "```"])

    return "\n".join(parts).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.directory).expanduser().resolve()

    if not root.exists():
        print(f"error: directory not found: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    allowed_extensions = parse_extensions(args.extensions)
    excluded_dirs = set(DEFAULT_EXCLUDED_DIRS)
    excluded_paths = {
        normalize_path_token(entry)
        for entry in args.exclude
        if normalize_path_token(entry)
    }
    gitignore_rules = load_gitignore_rules(root)

    snapshot = build_snapshot(
        root=root,
        allowed_extensions=allowed_extensions,
        excluded_dirs=excluded_dirs,
        excluded_paths=excluded_paths,
        gitignore_rules=gitignore_rules,
        max_size_kb=args.max_size,
        include_tree=not args.no_tree,
        include_contents=not args.no_contents,
        quiet=args.quiet,
    )

    if args.output:
        output_path = Path(args.output).expanduser()
        try:
            output_path.write_text(snapshot, encoding="utf-8")
        except OSError as exc:
            print(f"error: failed to write output file {output_path}: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
