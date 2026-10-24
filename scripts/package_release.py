"""Build vendorable source assets and SHA256SUMS; no runtime build dependencies."""
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    names = []
    for source, name in (("lunar_lander.py", "lunar_lander.py"), ("LICENSE", "LICENSE"),
                         ("profiles/netbbs.json", "netbbs.json"), ("docs/operations.md", "OPERATIONS.md"),
                         ("docs/acceptance.md", "ACCEPTANCE.md")):
        data = (ROOT / source).read_bytes()
        if b"\r\n" in data:
            raise SystemExit(f"{source}: CRLF detected; build from an LF checkout")
        shutil.copyfile(ROOT / source, output / name)
        names.append(name)
    checksums = "".join(f"{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}\n" for name in names)
    (output / "SHA256SUMS").write_bytes(checksums.encode("ascii"))
    print(checksums, end="")


if __name__ == "__main__":
    main()
