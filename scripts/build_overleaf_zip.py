#!/usr/bin/env python3
"""Build a standalone Overleaf-upload ZIP from paper/overleaf/ only.

ZIP root contains main.tex (no nested folder). Excludes repository harness
folders (results/, scripts/, etc.) that are not required to compile the paper.
"""
from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "overleaf"
OUT_ZIP = ROOT / "ECN_Tier1_IEEE_Overleaf.zip"
STAGING = ROOT / "paper" / "_overleaf_zip_staging"

# Paths relative to paper/overleaf that belong in the Overleaf project
INCLUDE_FILES = [
    "main.tex",
    "references.bib",
    "README.md",
]
INCLUDE_DIRS = [
    "sections",
    "tables",
    "figures",
    "supplementary",
]
# Optional class/style if present in source
OPTIONAL_STYLE = [
    "IEEEtran.cls",
    "IEEEtran.bst",
]

EXCLUDE_NAME_PARTS = {
    "__pycache__",
    ".git",
}
EXCLUDE_SUFFIXES = {
    ".aux",
    ".bbl",
    ".blg",
    ".log",
    ".out",
    ".synctex.gz",
    ".toc",
    ".lof",
    ".lot",
}


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_NAME_PARTS for part in path.parts):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    # CSV artifacts in tables/ are not required by LaTeX
    if path.suffix.lower() == ".csv":
        return True
    # Do not ship compiled PDF inside upload ZIP
    if path.name == "main.pdf":
        return True
    return False


def stage() -> Path:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)

    for name in INCLUDE_FILES:
        src = SRC / name
        if src.exists():
            shutil.copy2(src, STAGING / name)

    for dname in INCLUDE_DIRS:
        src = SRC / dname
        if not src.exists():
            continue
        dst = STAGING / dname
        for f in src.rglob("*"):
            if f.is_dir():
                continue
            if should_skip(f):
                continue
            rel = f.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)

    for name in OPTIONAL_STYLE:
        src = SRC / name
        if src.exists():
            shutil.copy2(src, STAGING / name)

    assert (STAGING / "main.tex").exists(), "main.tex missing at ZIP root staging"
    assert (STAGING / "references.bib").exists(), "references.bib missing"
    assert (STAGING / "sections").is_dir(), "sections/ missing"
    assert (STAGING / "figures").is_dir(), "figures/ missing"
    assert (STAGING / "tables").is_dir(), "tables/ missing"
    return STAGING


def write_zip(staging: Path) -> Path:
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in staging.rglob("*"):
            if f.is_dir():
                continue
            arc = f.relative_to(staging).as_posix()
            zf.write(f, arcname=arc)
    return OUT_ZIP


def verify_zip_layout(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "main.tex" in names, "ZIP root must contain main.tex"
    assert "references.bib" in names
    assert any(n.startswith("sections/") for n in names)
    assert any(n.startswith("figures/") for n in names)
    assert any(n.startswith("tables/") for n in names)
    # Must NOT contain repo harness folders
    forbidden_roots = ("benchmark/", "framework/", "evaluation/", "baselines/", "tests/")
    for fr in forbidden_roots:
        assert not any(n.startswith(fr) for n in names), f"forbidden {fr}"
    # Prefer no results/scripts at ZIP root either
    assert not any(n.startswith("results/") for n in names)
    assert not any(n.startswith("scripts/") for n in names)
    print("zip_entries", len(names))
    print("zip_root_ok", True)


def compile_clean_extract(zip_path: Path) -> None:
    """Extract to a fresh folder and compile like a new Overleaf project."""
    extract = ROOT / "paper" / "_overleaf_compile_check"
    if extract.exists():
        shutil.rmtree(extract)
    extract.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract)
    assert (extract / "main.tex").exists()
    cmds = [
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
        ["bibtex", "main"],
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
    ]
    for cmd in cmds:
        print("RUN", " ".join(cmd))
        subprocess.check_call(cmd, cwd=str(extract))
    pdf = extract / "main.pdf"
    assert pdf.exists() and pdf.stat().st_size > 10_000
    print("compile_ok", pdf.stat().st_size)


def main() -> None:
    staging = stage()
    zip_path = write_zip(staging)
    verify_zip_layout(zip_path)
    compile_clean_extract(zip_path)
    print("wrote", zip_path)
    print("bytes", zip_path.stat().st_size)


if __name__ == "__main__":
    main()
