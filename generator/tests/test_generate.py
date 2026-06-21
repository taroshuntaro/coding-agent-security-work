import unittest
import tempfile
import json
from pathlib import Path
import generate
from agentsec import questions


def scripted(inputs):
    it = iter(inputs)
    return lambda prompt="": next(it)


def sink():
    out = []
    return out, (lambda *a, **k: out.append(" ".join(str(x) for x in a)))


class TestAskQuestion(unittest.TestCase):
    def _q(self, key):
        return next(q for q in questions.QUESTIONS if q["key"] == key)

    def test_help_then_value(self):
        out, pr = sink()
        val = generate.ask_question(self._q("level"), scripted(["?", "L3"]), pr)
        self.assertEqual(val, "L3")
        self.assertTrue(any("迷ったら L2" in line for line in out))

    def test_invalid_then_default(self):
        out, pr = sink()
        val = generate.ask_question(self._q("level"), scripted(["L9", ""]), pr)
        self.assertEqual(val, "L2")


class TestCollectInteractive(unittest.TestCase):
    def test_unknown_stack_warns_and_reasks(self):
        # 製品2, level, plan, stacks(不正→正), domains, extra, container, 4 redline questions
        inputs = ["y", "y", "L2", "team",
                  "npm,rust", "npm",          # stacks: 未知 rust → 再入力
                  "github.com", "",
                  "y", "n", "n", "n", "n"]
        out, pr = sink()
        profile = generate.collect_interactive(scripted(inputs), pr)
        self.assertEqual(profile["stacks"], ["npm"])
        self.assertTrue(any("rust" in line for line in out))
        self.assertEqual(profile["level"], "L2")
        self.assertEqual(profile["products"], ["claude", "codex"])


class TestMainSaveProfile(unittest.TestCase):
    def test_save_profile_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            prof_path = Path(d) / "p.json"
            src = {"products": ["claude"], "level": "L2", "plan": "personal",
                   "stacks": ["npm"], "allowed_domains": ["github.com"],
                   "extra_deny_paths": [], "use_container": False}
            (Path(d) / "in.json").write_text(json.dumps(src), encoding="utf-8")
            rc = generate.main(["--profile", str(Path(d) / "in.json"),
                                "--output", str(Path(d) / "out"),
                                "--save-profile", str(prof_path)])
            self.assertEqual(rc, 0)
            saved = json.loads(prof_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["level"], "L2")


class TestMainOverwriteGuard(unittest.TestCase):
    def test_nonempty_output_without_force_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            out.mkdir()
            (out / "existing.txt").write_text("x", encoding="utf-8")
            (Path(d) / "in.json").write_text(json.dumps(
                {"products": ["claude"], "level": "L2", "plan": "personal",
                 "stacks": ["npm"], "allowed_domains": ["github.com"],
                 "extra_deny_paths": [], "use_container": False}), encoding="utf-8")
            rc = generate.main(["--profile", str(Path(d) / "in.json"),
                                "--output", str(out)])
            self.assertEqual(rc, 2)
