"""Keep local scratch bounded (README, "Local disk hygiene").

Scratch left in local worktrees once grew to several million files on this
development host and took it down; recovery took a day and an offline disk
check. Moved to the system temp folder, it later passed half a million
entries there and had to be cleared by hand. Two checks guard this repo:

- the checkout's ignored scratch (.task, .test-tmp, .pytest_cache) must hold
  at most LIMIT files; above that, run `python scripts/clean_scratch.py`
  and prune .task;
- no code may make a temp folder or file that nothing removes: use
  tempfile.TemporaryDirectory (with `with` or addCleanup), never mkdtemp,
  mkstemp or delete=False.
"""
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRATCH_DIRS = (".task", ".test-tmp", ".pytest_cache")
DEFAULT_LIMIT = 50_000
LIMIT_VARIABLE = "LUNAR_LANDER_SCRATCH_LIMIT"
LEAKS = re.compile(r"\bmk[ds]temp\(|\bdelete\s*=\s*False")


def scratch_limit():
    return int(os.environ.get(LIMIT_VARIABLE, DEFAULT_LIMIT))


def count_files(root, stop_after):
    """Files under root, counting at most stop_after + 1 so a huge tree stays cheap."""
    count, pending = 0, [root]
    while pending:
        try:
            entries = os.scandir(pending.pop())
        except OSError:
            continue
        with entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(entry.path)
                        continue
                except OSError:
                    continue
                count += 1
                if count > stop_after:
                    return count
    return count


class DiskHygieneTests(unittest.TestCase):
    def test_scratch_is_bounded(self):
        limit = scratch_limit()
        total = 0
        for name in SCRATCH_DIRS:
            total += count_files(ROOT / name, limit - total)
        self.assertLessEqual(total, limit,
                             f"This checkout holds more than {limit:,} scratch files in {', '.join(SCRATCH_DIRS)}. "
                             f"Run `python scripts/clean_scratch.py` and prune .task (commit evidence you need under "
                             f"docs/ first). {LIMIT_VARIABLE} raises the limit for one run.")

    def test_no_temp_folder_is_left_behind(self):
        own = Path(__file__).resolve()
        sources = [ROOT / "lunar_lander.py", *sorted((ROOT / "tests").glob("*.py")), *sorted((ROOT / "scripts").glob("*.py"))]
        leaks = [f"{path.relative_to(ROOT).as_posix()}:{number}"
                 for path in sources if path.resolve() != own
                 for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                 if LEAKS.search(line.split("#", 1)[0])]
        self.assertEqual(leaks, [], "Temp files nothing removes: use tempfile.TemporaryDirectory with `with` or addCleanup.")


if __name__ == "__main__":
    unittest.main()
