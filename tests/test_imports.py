"""Verify that importing a demo does not execute its main workflow."""

import runpy
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIRECTORY = REPOSITORY_ROOT / "demos"
sys.path.insert(0, str(DEMOS_DIRECTORY))


class DemoImportTests(unittest.TestCase):
    def test_all_demo_modules_import_without_running_main(self) -> None:
        for demo_path in sorted(DEMOS_DIRECTORY.glob("[0-9][0-9]_*.py")):
            with self.subTest(demo=demo_path.name):
                runpy.run_path(demo_path, run_name="import_check")


if __name__ == "__main__":
    unittest.main()
