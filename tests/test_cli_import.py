import importlib
import unittest


class CliImportTests(unittest.TestCase):
    def test_cli_imports_with_report_renderers(self):
        importlib.import_module("lottery_sim.cli")


if __name__ == "__main__":
    unittest.main()
