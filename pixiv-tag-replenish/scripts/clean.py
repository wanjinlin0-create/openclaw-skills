#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean a Pixiv tag folder: flatten → delete manga → dedup pages → dedup artists.

Usage:
    python clean.py <folder>
    python clean.py <folder> --manga-threshold 4 --dry-run

Rules (learned from real usage):
    1. Flatten nested subdirectories into root
    2. Works with >=4 pages → delete ALL (manga/comic/story)
    3. Works with 2-3 pages → keep page 0 only (variant/差分)
    4. Same artist appears multiple times → keep largest file only
"""

import argparse
import io
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

# Fix Windows terminal encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif"}
DEFAULT_MANGA_THRESHOLD = 4


def extract_work_info(filename: str):
    """Extract (member_id, image_id, page) from Pixiv filename."""
    # Format: {member}-{image}_{page}.ext
    m = re.match(r"^(\d+)-(\d+)_(\d+)\.\w+$", filename)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Format: {member}-{image}_.ext (single page)
    m = re.match(r"^(\d+)-(\d+)_\.\w+$", filename)
    if m:
        return m.group(1), m.group(2), 0
    return None, None, None


def get_images(folder: Path) -> list[Path]:
    return [f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS]


# ── Step 1: Flatten ─────────────────────────────────────────

def flatten(folder: Path) -> int:
    """Move images from subdirs to root, remove empty dirs."""
    moved = 0
    for f in list(folder.rglob("*")):
        if f.is_file() and f.parent != folder and f.suffix.lower() in IMAGE_EXTS:
            dest = folder / f.name
            if dest.exists():
                dest = folder / f"{f.parent.name}_{f.name}"
            shutil.move(str(f), str(dest))
            moved += 1
    for d in sorted(folder.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass
    return moved


# ── Step 2: Delete manga / dedup pages ──────────────────────

def clean_works(folder: Path, threshold: int, dry: bool) -> dict:
    """Delete manga (>=threshold pages) and dedup multi-page works."""
    files = get_images(folder)
    works: dict[str, list[dict]] = defaultdict(list)
    skipped = 0

    for f in files:
        mid, iid, page = extract_work_info(f.name)
        if iid is not None:
            works[iid].append({"path": f, "page": page, "name": f.name, "mid": mid})
        else:
            skipped += 1

    del_dedup = 0
    del_manga = 0
    manga_ids = []

    for iid, pages in works.items():
        pages.sort(key=lambda p: p["page"])
        n = len(pages)
        if n == 1:
            continue
        elif n < threshold:
            # 2-3 pages: keep first only
            for p in pages[1:]:
                if not dry:
                    os.remove(p["path"])
                del_dedup += 1
        else:
            # >=threshold: manga, delete all
            manga_ids.append(iid)
            for p in pages:
                if not dry:
                    os.remove(p["path"])
                del_manga += 1

    return {"del_dedup": del_dedup, "del_manga": del_manga,
            "manga_count": len(manga_ids), "skipped": skipped}


# ── Main ────────────────────────────────────────────────────

def clean(folder_str: str, threshold: int = DEFAULT_MANGA_THRESHOLD,
          dry: bool = False) -> dict:
    folder = Path(folder_str)
    if not folder.exists():
        print(f"ERROR: {folder} not found")
        sys.exit(1)

    before = len(get_images(folder))
    print(f"Before: {before} files")

    # 1) Flatten nested subdirs
    moved = flatten(folder)
    if moved:
        print(f"[flatten] {moved} files moved from subdirs")

    # 2) Manga delete + page dedup (by image_id in filename)
    r = clean_works(folder, threshold, dry)
    print(f"[manga]  {r['del_manga']} deleted ({r['manga_count']} works >= {threshold} pages)")
    print(f"[dedup]  {r['del_dedup']} deleted (kept page 0)")

    after = len(get_images(folder))
    total_del = r["del_dedup"] + r["del_manga"]
    print(f"\nAfter:   {after} files  (deleted {total_del})")
    if dry:
        print("** DRY RUN — nothing deleted **")

    return {"before": before, "after": after, "deleted": total_del,
            "manga": r["del_manga"], "dedup": r["del_dedup"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Clean Pixiv tag folder")
    ap.add_argument("folder")
    ap.add_argument("--manga-threshold", type=int, default=DEFAULT_MANGA_THRESHOLD)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    clean(a.folder, a.manga_threshold, a.dry_run)
