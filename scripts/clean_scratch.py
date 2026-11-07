"""Remove this checkout's local scratch, or report how much there is.

    python scripts/clean_scratch.py            # remove caches: .test-tmp, .pytest_cache, __pycache__
    python scripts/clean_scratch.py --report   # file counts for the checkout, its worktrees, .task and temp

Scratch left in local worktrees once grew to several million files on this
host and took it down; moved to the system temp folder, it passed half a
million entries there too. See "Local disk hygiene" in the README.

Cleaning deletes only ignored, reproducible caches, never `.venv`, never
tracked files and never `.task` (it holds captures and release evidence:
commit what you need under docs/, then delete the rest by hand). A symlink
is removed itself, never its target. The report deletes nothing.
"""
import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_disk_hygiene import LIMIT_VARIABLE, SCRATCH_DIRS, count_files, scratch_limit  # noqa: E402

CACHE_DIRS = (".test-tmp", ".pytest_cache")
SKIP = {".git", ".venv", ".worktrees", "node_modules"}


def scratch_paths(root):
    found = [root / name for name in CACHE_DIRS if (root / name).exists()]
    for top, dirs, _ in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and d not in CACHE_DIRS and d != ".task"]
        for d in list(dirs):
            if d == "__pycache__" or d.endswith(".egg-info"):
                found.append(Path(top) / d)
                dirs.remove(d)
    return found


def remove(path):
    failed = []

    def retry(function, name, _error):
        try:
            os.chmod(name, stat.S_IWRITE)
            function(name)
        except OSError:
            failed.append(name)
    if path.is_symlink():
        try:
            path.unlink()
        except OSError:
            failed.append(str(path))
    elif path.is_dir():
        shutil.rmtree(path, onexc=retry) if sys.version_info >= (3, 12) else shutil.rmtree(path, onerror=retry)
    else:
        retry(os.remove, str(path), None)
    return failed


def clean(root):
    removed, failed = 0, []
    for path in scratch_paths(root):
        refused = remove(path)
        failed += refused
        removed += not refused
    print(f"{root}: {removed} cache folders removed, {len(failed)} paths could not be deleted.")
    for name in failed[:20]:
        print(f"  {name}")
    return 1 if failed else 0


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True).stdout.strip()


def count_tree(tree):
    total = 0
    for entry in os.scandir(tree):
        if entry.name in SKIP:
            continue
        total += count_files(Path(entry.path), 10**9) if entry.is_dir(follow_symlinks=False) else 1
    return total


def report(root, limit):
    flagged = 0
    trees = [Path(line.split(" ", 1)[1]) for line in git(root, "worktree", "list", "--porcelain").splitlines()
             if line.startswith("worktree ")] or [root]
    for tree in trees:
        total = count_tree(tree)
        scratch = sum(count_files(tree / name, 10**9) for name in SCRATCH_DIRS)
        notes = [f"OVER {limit:,}"] if scratch > limit else []
        if tree.resolve() != root.resolve() and not git(tree, "status", "--porcelain") and \
                subprocess.run(["git", "-C", str(tree), "merge-base", "--is-ancestor", "HEAD", "origin/main"]).returncode == 0:
            notes.append("no commits of its own: `git worktree remove` it once its PR has merged")
        flagged += scratch > limit
        print(f"{total:>9,} files, {scratch:>7,} scratch  {tree}  {'; '.join(notes)}")
    temp = Path(tempfile.gettempdir())
    print(f"{sum(1 for _ in temp.iterdir()):>9,} entries in the system temp folder, {temp}")
    return 1 if flagged else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", action="store_true", help="report file counts; delete nothing")
    parser.add_argument("--limit", type=int, default=None, help=f"scratch files before a tree is flagged ({LIMIT_VARIABLE})")
    args = parser.parse_args(argv)
    return report(ROOT, args.limit or scratch_limit()) if args.report else clean(ROOT)


if __name__ == "__main__":
    sys.exit(main())
