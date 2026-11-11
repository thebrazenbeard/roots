"""Hostile source-only regression probes; do not execute injected content."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "security"))
from check_editor_source_safety import check_tree, parse_jsonc  # noqa: E402


class JSONCAdversarialTests(unittest.TestCase):
    def test_bom_comments_trailing_comma(self):
        raw = b'\xef\xbb\xbf{"tasks": [ // note\n {"label":"a",},],}'
        self.assertEqual(parse_jsonc(raw), {"tasks": [{"label": "a"}]})

    def test_quoted_comments_are_not_removed(self):
        self.assertEqual(parse_jsonc(b'{"url":"https://example.org/a,b]",}'), {"url": "https://example.org/a,b]"})

    def test_duplicate_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_jsonc(b'{"tasks":[],"tasks":[]}')

    def test_leading_array_comma_is_not_silently_removed(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_jsonc(b'{"tasks":[,]}')

    def test_leading_commented_array_comma_is_not_silently_removed(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_jsonc(b'[/*x*/,]')

    def test_dangling_object_value_comma_rejected(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_jsonc(b'{"a":,}')

    def test_unterminated_block_comment_rejected(self):
        with self.assertRaisesRegex(ValueError, "unclosed"):
            parse_jsonc(b'{"tasks": [] /*')


class EditorSourceGuardAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="roots-source-guard-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / ".vscode", self.root / ".vscode")
        shutil.copytree(ROOT / "public" / "fonts", self.root / "public" / "fonts")
        shutil.copy2(ROOT / ".gitignore", self.root / ".gitignore")

    def _set_tasks(self, content):
        (self.root / ".vscode" / "tasks.json").write_bytes(content)

    def _set_settings(self, value):
        (self.root / ".vscode" / "settings.json").write_text(json.dumps(value), encoding="utf-8")

    def _assert_blocked(self, fragment):
        self.assertIn(fragment, "\n".join(check_tree(self.root)))

    def test_clean_merge_tree_passes(self):
        self.assertEqual(check_tree(self.root), [])

    def test_bom_folder_open_rejected(self):
        self._set_tasks(b'\xef\xbb\xbf{"tasks":[{"runOptions":{"runOn":"folderOpen"}}]}')
        self._assert_blocked("folderOpen")

    def test_duplicate_key_cannot_shadow_folder_open(self):
        self._set_tasks(b'{"tasks":[{"runOn":"folderOpen"}],"tasks":[]}')
        self._assert_blocked("duplicate JSONC key")

    def test_nested_windows_folder_open(self):
        self._set_tasks(b'{"windows":{"tasks":[{"runOptions":{"runOn":"folderOpen"}}]}}')
        self._assert_blocked("folderOpen")

    def test_recursive_workspace_folder_open(self):
        workspace = self.root / "subproject" / "sample.code-workspace"
        workspace.parent.mkdir()
        workspace.write_text('{"tasks":{"windows":{"tasks":[{"runOn":"folderOpen"}]}}}', encoding="utf-8")
        self._assert_blocked("folderOpen")

    def test_uppercase_workspace_extension_folder_open(self):
        workspace = self.root / "subproject" / "UPPER.CODE-WORKSPACE"
        workspace.parent.mkdir()
        workspace.write_text('{"tasks":[{"runOptions":{"runOn":"folderOpen"}}]}', encoding="utf-8")
        self._assert_blocked("folderOpen")

    def test_nested_vscode_tasks_folder_open(self):
        task = self.root / "subproject" / ".vscode" / "tasks.json"
        task.parent.mkdir(parents=True)
        task.write_text('{"tasks":[{"runOptions":{"runOn":"folderOpen"}}]}', encoding="utf-8")
        self._assert_blocked("folderOpen")

    def test_case_variant_vscode_tasks_folder_open(self):
        task = self.root / ".VSCODE" / "TASKS.JSON"
        task.parent.mkdir(parents=True)
        task.write_text('{"tasks":[{"runOptions":{"runOn":"folderOpen"}}]}', encoding="utf-8")
        self._assert_blocked("folderOpen")
        self._assert_blocked("case-variant editor directory")

    def test_inherited_command_and_args_font(self):
        self._set_tasks(b'{"windows":{"command":"node","args":["./public/fonts/fa-solid-600.ttf"]},"tasks":[]}')
        self._assert_blocked("font referenced")

    def test_windows_font_path_slashes(self):
        self._set_tasks(b'{"tasks":[{"command":"node","args":["public\\\\fonts\\\\fa-solid-600.ttf"]}]}')
        self._assert_blocked("font referenced")

    def test_settings_embedded_tasks(self):
        self._set_settings({"task.allowAutomaticTasks": "off", "tasks": {"runOn": "folderOpen"}})
        self._assert_blocked("embedded tasks")

    def test_settings_automatic_on(self):
        self._set_settings({"task.allowAutomaticTasks": "on"})
        self._assert_blocked("automatic editor tasks enabled")

    def test_settings_automatic_boolean(self):
        self._set_settings({"task.allowAutomaticTasks": True})
        self._assert_blocked("automatic editor tasks enabled")

    def test_nested_settings_autostart(self):
        settings = self.root / ".vscode" / "windows" / "settings.json"
        settings.parent.mkdir()
        settings.write_text('{"task.allowAutomaticTasks":true}', encoding="utf-8")
        self._assert_blocked("automatic editor tasks enabled")

    def test_case_variant_settings_with_embedded_tasks(self):
        settings = self.root / ".vscode" / "SETTINGS.JSON"
        settings.write_text('{"task.allowAutomaticTasks":"off","tasks":[]}', encoding="utf-8")
        self._assert_blocked("embedded tasks in editor settings")
        self._assert_blocked("case-variant editor file")

    def test_unapproved_font_like_js_even_woff(self):
        (self.root / "public" / "fonts" / "fa-solid-600.ttf").write_bytes(b'// malicious-looking but NEVER executed')
        self._assert_blocked("unapproved font asset")

    def test_approved_ttf_content_tamper(self):
        path = self.root / "public" / "fonts" / "fa-solid-900.ttf"
        path.write_bytes(path.read_bytes() + b'/* appended */')
        self._assert_blocked("font asset hash mismatch")

    def test_svg_crlf_only_accepted(self):
        path = self.root / "public" / "fonts" / "fa-solid-900.svg"
        content = path.read_bytes()
        self.assertIn(b"\n", content)
        path.write_bytes(content.replace(b"\n", b"\r\n"))
        self.assertEqual(check_tree(self.root), [])

    def test_svg_crlf_plus_appended_script_rejected(self):
        path = self.root / "public" / "fonts" / "fa-solid-900.svg"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b"<script>danger</script>")
        self._assert_blocked("font asset hash mismatch")

    def test_font_readme_crlf_only_accepted(self):
        path = self.root / "public" / "fonts" / "README.md"
        content = path.read_bytes()
        self.assertIn(b"\n", content)
        path.write_bytes(content.replace(b"\n", b"\r\n"))
        self.assertEqual(check_tree(self.root), [])

    def test_font_readme_crlf_plus_content_change_rejected(self):
        path = self.root / "public" / "fonts" / "README.md"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b"Tampered\r\n")
        self._assert_blocked("font asset hash mismatch")

    def test_missing_font_directory_rejected(self):
        shutil.rmtree(self.root / "public" / "fonts")
        self._assert_blocked("missing or symlinked public/fonts")

    def test_missing_legitimate_font_rejected(self):
        (self.root / "public" / "fonts" / "fa-solid-900.woff2").unlink()
        self._assert_blocked("missing approved font asset")

    def test_symlinked_font_rejected(self):
        path = self.root / "public" / "fonts" / "fa-solid-900.ttf"
        target = self.root / "target.ttf"
        target.write_bytes(path.read_bytes())
        path.unlink()
        try:
            path.symlink_to(target)
        except OSError:
            self.skipTest("symlinks unavailable on this host")
        self._assert_blocked("symlink/non-file font")

    def test_symlinked_workspace_rejected(self):
        destination = self.root / "external.code-workspace"
        destination.write_text('{}', encoding="utf-8")
        path = self.root / "sample.code-workspace"
        try:
            path.symlink_to(destination)
        except OSError:
            self.skipTest("symlinks unavailable on this host")
        self._assert_blocked("symlinked workspace")

    def test_ignore_env_removal_rejected(self):
        path = self.root / ".gitignore"
        path.write_text(path.read_text().replace(".env\n", ""), encoding="utf-8")
        self._assert_blocked(".gitignore missing .env")

    def test_ignore_payload_hiding_rejected(self):
        path = self.root / ".gitignore"
        path.write_text(path.read_text() + "\npublic/fonts\n", encoding="utf-8")
        self._assert_blocked("suspicious newly ignored path")

    def test_ignore_slash_and_case_variant_payload_hiding_rejected(self):
        path = self.root / ".gitignore"
        path.write_text(path.read_text() + "\npublic/fonts/\n.VSCODE/\nnode_modules/\n", encoding="utf-8")
        self._assert_blocked("suspicious newly ignored path")
        self._assert_blocked(".gitignore differs from the explicit new ROOTS safe policy")


if __name__ == "__main__":
    unittest.main()
