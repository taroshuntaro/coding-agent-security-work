import unittest
import tempfile
import os
import json
from agentsec import profile


class TestProfile(unittest.TestCase):
    def _valid(self):
        return {"products": ["claude"], "level": "L2", "plan": "team",
                "stacks": ["npm"], "allowed_domains": ["github.com"],
                "extra_deny_paths": [], "use_container": True}

    def test_validate_ok(self):
        profile.validate(self._valid())  # raises nothing

    def test_validate_missing_key(self):
        p = self._valid()
        del p["level"]
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_validate_bad_level(self):
        p = self._valid()
        p["level"] = "L9"
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.json")
            profile.save(path, self._valid())
            self.assertEqual(profile.load(path)["level"], "L2")

    def test_build_record_has_hashes_and_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "settings.json")
            with open(f, "w") as fh:
                fh.write("{}")
            rec = profile.build_record(self._valid(), {"settings.json": f}, [])
            self.assertIn("generated_at", rec)
            self.assertEqual(len(rec["files"]["settings.json"]), 64)  # sha256 hex
            self.assertIn("product_versions", rec)

    def test_validate_accepts_optional_base_image(self):
        p = self._valid()
        p["base_image"] = "python:3.12-slim-bookworm"
        profile.validate(p)  # raises nothing

    def test_validate_rejects_non_string_base_image(self):
        p = self._valid()
        p["base_image"] = 123
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_base_image_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.json")
            p = self._valid()
            p["base_image"] = "golang:1.22-bookworm"
            profile.save(path, p)
            self.assertEqual(profile.load(path)["base_image"], "golang:1.22-bookworm")

    def test_claude_min_version_must_be_str(self):
        p = self._valid()
        p["claude_min_version"] = 1
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_claude_min_version_str_ok(self):
        p = self._valid()
        p["claude_min_version"] = "2.1.163"
        profile.validate(p)  # raises しなければ OK
