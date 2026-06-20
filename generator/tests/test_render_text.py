import unittest
from agentsec import render_text


class TestRenderText(unittest.TestCase):
    def test_dockerfile_renders_nonroot(self):
        out = render_text.render("container/Dockerfile.tmpl",
                                 {"base_image": "node:20-bookworm-slim"})
        self.assertIn("node:20-bookworm-slim", out)
        self.assertIn("USER", out)

    def test_compose_has_security_opts(self):
        out = render_text.render("container/docker-compose.yml.tmpl",
                                 {"service_name": "dev"})
        self.assertIn("no-new-privileges", out)
        self.assertIn("read_only", out)

    def test_missing_key_raises(self):
        with self.assertRaises(KeyError):
            render_text.render("container/Dockerfile.tmpl", {})
