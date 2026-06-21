import unittest
from agentsec import render_text


class TestPolicySheet(unittest.TestCase):
    def _render(self):
        return render_text.render("policy/policy-sheet.md.tmpl", {
            "level": "L2", "plan": "team", "products": "claude, codex",
            "use_container": "True", "base_image": "node:20-bookworm-slim",
            "deny_paths": "./.env", "allowed_domains": "github.com",
            "deviations_block": "（なし）",
        })

    def test_sections_are_sequential(self):
        out = self._render()
        self.assertIn("## 4. ネットワーク", out)
        self.assertIn("## 5. 逸脱事項", out)
        self.assertNotIn("## 12.", out)
        self.assertNotIn("## 5. ネットワーク", out)
