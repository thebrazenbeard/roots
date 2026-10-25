"""Static checks for editor-startup safety; do not execute workspace tasks."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EditorStartupSafetyTests(unittest.TestCase):
    def test_tasks_parse_and_disable_folder_open_execution(self):
        text = (ROOT / ".vscode" / "tasks.json").read_text(encoding="utf-8")
        tasks = json.loads(text)
        self.assertEqual(tasks.get("tasks"), [])
        self.assertIsNone(re.search(r'"runOn"\s*:\s*"folderOpen"', text))
        self.assertIsNone(re.search(r"\bnode\s+[^\n]*public/fonts/", text))

    def test_workspace_does_not_claim_user_task_permission(self):
        settings = json.loads((ROOT / ".vscode" / "settings.json").read_text(
            encoding="utf-8"
        ))
        # Automatic-task permission belongs to VS Code user/application scope.
        self.assertNotIn("task.allowAutomaticTasks", settings)
        self.assertNotIn("tasks", settings)

    def test_disguised_script_not_a_font(self):
        self.assertFalse((ROOT / "public/fonts/fa-solid.lkf").exists())


if __name__ == "__main__":
    unittest.main()
