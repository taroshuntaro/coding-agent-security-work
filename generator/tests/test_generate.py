import unittest
import tempfile
import json
from pathlib import Path
import generate
from agentsec import questions, detect


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
        with tempfile.TemporaryDirectory() as d:
            # 製品2, level, plan, stacks(不正→正), domains, extra, container, 4 redline
            inputs = ["y", "y", "L2", "team",
                      "npm,rust", "npm",          # stacks: 未知 rust → 再入力
                      "github.com", "",
                      "y", "n", "n", "n", "n",
                      ""]                          # 推定 base-image を採用
            out, pr = sink()
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
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


class TestResolveStacksInteractive(unittest.TestCase):
    def test_detected_stacks_confirmed_with_empty_enter(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "package.json").write_text("", encoding="utf-8")
            out, pr = sink()
            # 確認に空 Enter（=はい）
            chosen = generate.resolve_stacks_interactive(d, scripted([""]), pr)
            self.assertEqual(chosen, ["npm"])
            self.assertTrue(any("npm" in line for line in out))

    def test_detected_rejected_then_manual_entry(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "package.json").write_text("", encoding="utf-8")
            out, pr = sink()
            # 確認に n（いいえ）→ 手動で go を入力
            chosen = generate.resolve_stacks_interactive(d, scripted(["n", "go"]), pr)
            self.assertEqual(chosen, ["go"])

    def test_unsupported_warns_and_falls_to_manual(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Cargo.toml").write_text("", encoding="utf-8")
            out, pr = sink()
            # 検出ゼロ（未対応のみ）→ 手動入力（空 Enter でスキップ）
            chosen = generate.resolve_stacks_interactive(d, scripted([""]), pr)
            self.assertEqual(chosen, [])
            self.assertTrue(any("rust" in line for line in out))

    def test_greenfield_zero_detection_manual_with_reask(self):
        with tempfile.TemporaryDirectory() as d:
            out, pr = sink()
            # 検出なし → 未知 rust で再質問 → npm
            chosen = generate.resolve_stacks_interactive(d, scripted(["npm,rust", "npm"]), pr)
            self.assertEqual(chosen, ["npm"])


class TestBaseImageResolution(unittest.TestCase):
    def test_single_stack_inferred_image_confirmed(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "go.mod").write_text("", encoding="utf-8")
            out, pr = sink()
            # 製品2, level, plan, [stacks: 検出 go を確認=空Enter],
            # domains, extra, container=y, 4 redline, base-image 確認=空Enter
            inputs = ["y", "y", "L2", "team",
                      "",                         # 検出 go を採用
                      "github.com", "",
                      "y", "n", "n", "n", "n",
                      ""]                          # 推定 base-image を採用
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertEqual(profile["stacks"], ["go"])
            self.assertEqual(profile["base_image"], "golang:1.22-bookworm")

    def test_no_container_uses_default_without_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "go.mod").write_text("", encoding="utf-8")
            out, pr = sink()
            # container=n のときは base-image を問わない（余分な入力なし）
            inputs = ["y", "y", "L2", "team",
                      "",                         # 検出 go を採用
                      "github.com", "",
                      "n", "n", "n", "n", "n"]    # container=n + 4 redline
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertEqual(profile["base_image"], detect.DEFAULT_BASE_IMAGE)

    def test_profile_base_image_used_on_regen(self):
        with tempfile.TemporaryDirectory() as d:
            src = {"products": ["claude"], "level": "L2", "plan": "personal",
                   "stacks": ["go"], "allowed_domains": ["github.com"],
                   "extra_deny_paths": [], "use_container": True,
                   "base_image": "golang:1.22-bookworm"}
            (Path(d) / "in.json").write_text(json.dumps(src), encoding="utf-8")
            rc = generate.main(["--profile", str(Path(d) / "in.json"),
                                "--output", str(Path(d) / "out")])
            self.assertEqual(rc, 0)
            dockerfile = (Path(d) / "out" / "Dockerfile").read_text(encoding="utf-8")
            self.assertIn("golang:1.22-bookworm", dockerfile)


class TestTargetDirEndToEnd(unittest.TestCase):
    def test_target_dir_detection_drives_generation(self):
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "proj"
            proj.mkdir()
            (proj / "go.mod").write_text("", encoding="utf-8")
            out = Path(d) / "out"
            # main は対話時 input() を直接使い注入できないため、検出→collect→
            # orchestrate を直接呼んで end-to-end を検証する（--profile 経路の
            # base-image 再現は Task 5 の test_profile_base_image_used_on_regen が担保）。
            # claude のみ, L2, personal, [検出 go 採用=空Enter],
            # domains, extra, container=y, 4 redline, base-image 採用=空Enter
            inputs = ["y", "n", "L2", "personal",
                      "",
                      "github.com", "",
                      "y", "n", "n", "n", "n",
                      ""]
            _, pr = sink()
            profile = generate.collect_interactive(scripted(inputs), pr,
                                                   target_dir=str(proj))
            self.assertEqual(profile["stacks"], ["go"])
            self.assertEqual(profile["base_image"], "golang:1.22-bookworm")
            generate.orchestrate.generate(profile, str(out), [], profile["base_image"])
            dockerfile = (out / "Dockerfile").read_text(encoding="utf-8")
            self.assertIn("golang:1.22-bookworm", dockerfile)
            self.assertIn("Bash(go test *)",
                          (out / "claude-code/.claude/settings.json").read_text(encoding="utf-8"))
