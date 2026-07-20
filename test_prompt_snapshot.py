import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


def load_module():
    spec = importlib.util.spec_from_file_location(
        "prompt_snapshot", Path(__file__).with_name("prompt-snapshot.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ps = load_module()


class PromptSnapshotTests(unittest.TestCase):
    def test_parse_extensions_defaults_and_custom(self):
        self.assertIn(".py", ps.parse_extensions(None))
        self.assertEqual(ps.parse_extensions(".py,.md,Dockerfile"), {".py", ".md", "Dockerfile"})

    def test_gitignore_simple_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("ignored.txt\nlogs/\n", encoding="utf-8")
            rules = ps.load_gitignore_rules(root)
            self.assertTrue(ps.gitignore_ignored(Path("ignored.txt"), is_dir=False, rules=rules))
            self.assertTrue(ps.gitignore_ignored(Path("logs"), is_dir=True, rules=rules))
            self.assertFalse(ps.gitignore_ignored(Path("keep.txt"), is_dir=False, rules=rules))

    def test_build_snapshot_includes_tree_and_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")

            text = ps.build_snapshot(
                root=root,
                allowed_extensions={".py", ".md"},
                excluded_dirs=set(ps.DEFAULT_EXCLUDED_DIRS),
                excluded_paths=set(),
                gitignore_rules=[],
                max_size_kb=100,
                include_tree=True,
                include_contents=True,
                quiet=True,
            )
            self.assertIn("# Project:", text)
            self.assertIn("## File Tree", text)
            self.assertIn("src/main.py", text)
            self.assertIn("```python", text)

    def test_truncates_large_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = "a" * 5000
            path = root / "big.txt"
            path.write_text(payload, encoding="utf-8")

            text, ok = ps.read_file_content(path, max_bytes=100, quiet=True)
            self.assertTrue(ok)
            self.assertIn("[... truncated ...]", text)

    def test_walk_project_single_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")

            walk = ps.walk_project(
                root=root,
                excluded_dirs=set(ps.DEFAULT_EXCLUDED_DIRS),
                excluded_paths=set(),
                gitignore_rules=[],
            )
            self.assertIn(f"{root.name}/", walk.tree_lines)
            self.assertEqual(len(walk.content_files), 2)
            names = {path.name for path in walk.content_files}
            self.assertEqual(names, {"main.py", "README.md"})

    def test_max_files_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for idx in range(5):
                (root / f"file{idx}.py").write_text(f"x = {idx}\n", encoding="utf-8")

            text = ps.build_snapshot(
                root=root,
                allowed_extensions={".py"},
                excluded_dirs=set(ps.DEFAULT_EXCLUDED_DIRS),
                excluded_paths=set(),
                gitignore_rules=[],
                max_size_kb=100,
                include_tree=False,
                include_contents=True,
                quiet=True,
                max_files=2,
            )
            self.assertIn("Snapshot truncated", text)
            self.assertIn("max-files limit (2)", text)
            self.assertEqual(text.count("### file"), 2)

    def test_max_output_mb_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large.py").write_text("x = " + ("a" * 5000) + "\n", encoding="utf-8")

            buffer = io.StringIO()
            stats = ps.write_snapshot(
                out=buffer,
                root=root,
                allowed_extensions={".py"},
                excluded_dirs=set(ps.DEFAULT_EXCLUDED_DIRS),
                excluded_paths=set(),
                gitignore_rules=[],
                max_size_kb=100,
                max_files=None,
                max_output_mb=0.001,
                include_tree=True,
                include_contents=True,
                quiet=True,
            )
            self.assertTrue(stats.truncated_by_max_output)
            output = buffer.getvalue()
            self.assertLessEqual(stats.output_bytes, int(0.001 * 1024 * 1024) + 64)

    def test_write_snapshot_streams_without_building_full_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hello.py").write_text("print('hi')\n", encoding="utf-8")

            buffer = io.StringIO()
            stats = ps.write_snapshot(
                out=buffer,
                root=root,
                allowed_extensions={".py"},
                excluded_dirs=set(ps.DEFAULT_EXCLUDED_DIRS),
                excluded_paths=set(),
                gitignore_rules=[],
                max_size_kb=100,
                max_files=None,
                max_output_mb=None,
                include_tree=True,
                include_contents=True,
                quiet=True,
            )
            output = buffer.getvalue()
            self.assertIn("hello.py", output)
            self.assertEqual(stats.files_included, 1)
            self.assertGreater(stats.output_bytes, 0)


if __name__ == "__main__":
    unittest.main()
