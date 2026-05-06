import os
import unittest
from pathlib import Path
from unittest.mock import patch

from lottery_sim import dashboard


class PackagingScriptTests(unittest.TestCase):
    def test_dashboard_command_uses_configured_powershell_executable(self):
        with patch.dict(os.environ, {"LOTTERY_POWERSHELL": "pwsh"}, clear=False):
            command = dashboard._dashboard_command("daily", "ssq", {})

        self.assertIsNotNone(command)
        self.assertEqual(command[0], "pwsh")

    def test_dashboard_scripts_can_call_packaged_exe_cli(self):
        daily = Path("scripts/daily.ps1").read_text(encoding="utf-8")
        update_data = Path("scripts/update_data.ps1").read_text(encoding="utf-8")

        self.assertIn("LOTTERY_CLI_EXE", daily)
        self.assertIn("--cli", daily)
        self.assertIn("LOTTERY_CLI_EXE", update_data)
        self.assertIn("--cli", update_data)

    def test_readme_documents_chinese_packaging_and_default_password(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("## Docker 服务", readme)
        self.assertIn("## Windows EXE 打包", readme)
        self.assertIn("默认账号密码", readme)
        self.assertIn("账号：admin", readme)
        self.assertIn("密码：admin", readme)
        self.assertIn("GitHub Release", readme)


if __name__ == "__main__":
    unittest.main()
