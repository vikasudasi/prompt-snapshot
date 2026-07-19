import importlib.util
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


if __name__ == "__main__":
    unittest.main()
