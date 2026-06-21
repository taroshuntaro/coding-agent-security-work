import unittest
import tempfile
from pathlib import Path
from agentsec import detect, stacks


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestDetectStacks(unittest.TestCase):
    def test_detects_markers_in_root(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "package.json")
            _touch(Path(d) / "go.mod")
            result = detect.detect_stacks(d)
            self.assertEqual(result["known"], ["go", "npm"])
            self.assertEqual(result["unsupported"], [])

    def test_csproj_glob_detects_dotnet(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "App.csproj")
            self.assertEqual(detect.detect_stacks(d)["known"], ["dotnet"])

    def test_pip_markers_dedup_to_single_key(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "pyproject.toml")
            _touch(Path(d) / "requirements.txt")
            self.assertEqual(detect.detect_stacks(d)["known"], ["pip"])

    def test_unions_across_subprojects(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "proj-a" / "package.json")
            _touch(Path(d) / "proj-b" / "go.mod")
            self.assertEqual(detect.detect_stacks(d)["known"], ["go", "npm"])

    def test_monorepo_nested_packages(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "packages" / "web" / "package.json")
            _touch(Path(d) / "services" / "api" / "go.mod")
            self.assertEqual(detect.detect_stacks(d)["known"], ["go", "npm"])

    def test_ignores_dependency_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "go.mod")
            _touch(Path(d) / "node_modules" / "dep" / "package.json")
            # node_modules は枝刈りされ npm を拾わない
            self.assertEqual(detect.detect_stacks(d)["known"], ["go"])

    def test_respects_max_depth(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "a" / "b" / "c" / "d" / "package.json")
            # max_depth=2 では深すぎて拾わない
            self.assertEqual(detect.detect_stacks(d, max_depth=2)["known"], [])

    def test_unsupported_markers_reported(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "Cargo.toml")
            _touch(Path(d) / "Gemfile")
            result = detect.detect_stacks(d)
            self.assertEqual(result["known"], [])
            self.assertEqual(result["unsupported"], ["ruby", "rust"])

    def test_empty_dir_returns_empty_lists(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(detect.detect_stacks(d), {"known": [], "unsupported": []})

    def test_missing_dir_returns_empty_lists(self):
        self.assertEqual(detect.detect_stacks("/no/such/dir/xyz"),
                         {"known": [], "unsupported": []})


class TestDetectConsistency(unittest.TestCase):
    def test_marker_values_are_known_stacks(self):
        for key in detect.MARKERS.values():
            self.assertIn(key, stacks.KNOWN)


if __name__ == "__main__":
    unittest.main()
