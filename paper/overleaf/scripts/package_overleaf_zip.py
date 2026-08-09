#!/usr/bin/env python3
"""Package a clean Overleaf ZIP of paper/overleaf (compile-ready).

Excludes .git, node_modules, __pycache__, venv, aux/log/synctex/out, .DS_Store.
Writes ECNetBench_ECNv3_Overleaf_Final.zip under paper/releases/ and paper/overleaf/.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "paper" / "overleaf"
OUT_DIR = ROOT / "paper" / "releases"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ZIP_NAME = "ECNetBench_ECNv3_Overleaf_Final.zip"

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".cache",
    ".ipynb_checkpoints",
}
SKIP_FILE_NAMES = {
    # Keep identifiable citation metadata out of the double-blind Overleaf ZIP.
    "CITATION.cff",
}
SKIP_SUFFIXES = {
    ".aux",
    ".log",
    ".out",
    ".toc",
    ".lof",
    ".lot",
    ".fls",
    ".fdb_latexmk",
    ".synctex.gz",
    ".bbl",
    ".blg",
    ".bcf",
    ".run.xml",
    ".nav",
    ".snm",
    ".vrb",
}
SKIP_ROOT_FILES = {
    "main.pdf",
    "ECNetBench_ECNv3_Overleaf_Final.zip",
}


def include(path: Path) -> bool:
    rel = path.relative_to(SRC)
    parts = rel.parts
    # skip if any parent directory is blacklisted
    for part in parts[:-1]:
        if part in SKIP_DIR_NAMES:
            return False
    if path.is_dir():
        return path.name not in SKIP_DIR_NAMES
    if path.name.startswith("."):
        return False
    if path.name in SKIP_FILE_NAMES:
        return False
    if path.name in SKIP_ROOT_FILES and path.parent == SRC:
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    if path.name.endswith("~"):
        return False
    return True


def main() -> None:
    assert (SRC / "main.tex").exists(), SRC
    dest = OUT_DIR / ZIP_NAME
    mirror = SRC / ZIP_NAME
    files = []
    for p in SRC.rglob("*"):
        if not p.is_file():
            continue
        if not include(p):
            continue
        # skip previous zip copies inside overleaf root
        if p.suffix.lower() == ".zip":
            continue
        files.append(p)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(files):
            arc = Path("ECNetBench_ECNv3_Overleaf") / p.relative_to(SRC)
            zf.write(p, arcname=str(arc).replace("\\", "/"))
    mirror.write_bytes(dest.read_bytes())
    print("wrote", dest, "files=", len(files), "bytes=", dest.stat().st_size)
    print("mirror", mirror)


if __name__ == "__main__":
    main()
