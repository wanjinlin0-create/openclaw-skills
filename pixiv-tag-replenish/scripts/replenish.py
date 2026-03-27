#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replenish a Pixiv tag collection v2:
  1. Search via Pixiv Ajax API with type=illust (no manga/ugoira)
  2. Filter to single-page works only
  3. Download originals directly with requests
  4. Run clean.py as safety net

Usage:
    python replenish.py <tag> [--pages 3] [--sort popular_d]
    python replenish.py --clean-only "\\\\NAS\\path"
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

# Fix Windows terminal encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
AGENT_DIR = SKILL_DIR.parent.parent
PIXIVUTIL_DIR = AGENT_DIR / "PixivUtil2"
CONFIG_FILE = PIXIVUTIL_DIR / "config.ini"
NAS_BASE = r"\\GBWSSforNAS\Download\pixiv\05_标签合集"

TAG_FOLDERS = {
    "眼鏡": "眼镜", "めがね": "眼镜",
    "黒タイツ": "黑丝", "黒スト": "黑丝",
    "白タイツ": "白丝", "白スト": "白丝",
    "ロリ": "萝莉", "loli": "萝莉",
    "JK": "JK",
    "水着": "泳装", "swimsuit": "泳装",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.pixiv.net/",
    "Accept": "application/json",
}

MAX_RETRIES = 3
RETRY_WAIT = 5


def resolve_folder(tag: str) -> str:
    return TAG_FOLDERS.get(tag, tag)


def read_cookie() -> str:
    """Read cookie string from PixivUtil2 config.ini."""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("cookie ="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("No cookie found in config.ini")


def search_tag(tag: str, pages: int, sort: str, cookie: str) -> list[dict]:
    """Search Pixiv with type=illust, return filtered work list."""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["Cookie"] = cookie

    all_works = []
    for p in range(1, pages + 1):
        url = (
            f"https://www.pixiv.net/ajax/search/artworks/{quote(tag)}"
            f"?word={quote(tag)}&order={sort}&mode=all"
            f"&s_mode=s_tag&type=illust&p={p}&lang=zh"
        )
        print(f"[search] page {p}/{pages} ...")

        for attempt in range(MAX_RETRIES):
            try:
                r = session.get(url, timeout=30)
                r.raise_for_status()
                data = r.json()
                break
            except Exception as e:
                print(f"  retry {attempt+1}: {e}")
                time.sleep(RETRY_WAIT)
        else:
            print(f"  FAILED page {p}, skipping")
            continue

        illusts = data.get("body", {}).get("illustManga", {}).get("data", [])
        if not illusts:
            # Try popular section for premium
            illusts = data.get("body", {}).get("popular", {}).get("permanent", [])
            illusts += data.get("body", {}).get("popular", {}).get("recent", [])

        for w in illusts:
            page_count = int(w.get("pageCount", 1))
            illust_type = w.get("illustType", 0)  # 0=illust, 1=manga, 2=ugoira

            # Only single-page illustrations
            if illust_type == 0 and page_count == 1:
                all_works.append({
                    "id": str(w["id"]),
                    "title": w.get("title", ""),
                    "user_id": str(w.get("userId", "")),
                    "user_name": w.get("userName", ""),
                    "url": w.get("url", ""),  # thumbnail URL (we'll get original later)
                })

        print(f"  found {len(illusts)} results, {len(all_works)} illust so far")
        time.sleep(2)

    return all_works


def get_original_url(illust_id: str, cookie: str) -> tuple[str, str]:
    """Get original image URL and member_id for an illustration."""
    url = f"https://www.pixiv.net/ajax/illust/{illust_id}/pages?lang=zh"
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["Cookie"] = cookie

    for attempt in range(MAX_RETRIES):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            pages = data.get("body", [])
            if pages:
                return pages[0]["urls"]["original"], ""
        except Exception as e:
            print(f"  detail retry {attempt+1}: {e}")
            time.sleep(RETRY_WAIT)

    return "", ""


def download_image(img_url: str, save_path: str, cookie: str) -> bool:
    """Download a single image with retries."""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["Cookie"] = cookie

    for attempt in range(MAX_RETRIES):
        try:
            r = session.get(img_url, timeout=60, stream=True)
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            size_kb = os.path.getsize(save_path) / 1024
            print(f"  OK {size_kb:.0f}KB -> {Path(save_path).name}")
            return True
        except Exception as e:
            print(f"  download retry {attempt+1}: {e}")
            time.sleep(RETRY_WAIT)

    return False


def make_filename(user_id: str, illust_id: str, ext: str) -> str:
    """Generate filename: {member_id}-{image_id}_.{ext}"""
    return f"{user_id}-{illust_id}_.{ext}"


def run_clean(folder: str, threshold: int = 4):
    clean_script = SCRIPT_DIR / "clean.py"
    subprocess.run([sys.executable, str(clean_script), folder,
                    "--manga-threshold", str(threshold)])


def main():
    ap = argparse.ArgumentParser(description="Replenish Pixiv tag (v2: API pre-filter)")
    ap.add_argument("tag", nargs="?", help="Pixiv tag to search")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--sort", default="popular_d")
    ap.add_argument("--manga-threshold", type=int, default=4)
    ap.add_argument("--clean-only", metavar="FOLDER")
    a = ap.parse_args()

    if a.clean_only:
        print(f"=== Clean only: {a.clean_only} ===")
        run_clean(a.clean_only, a.manga_threshold)
        return

    if not a.tag:
        ap.error("tag required (or use --clean-only)")

    folder_name = resolve_folder(a.tag)
    save_dir = os.path.join(NAS_BASE, folder_name)
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 50)
    print(f"Tag: {a.tag}  ->  {folder_name}")
    print(f"Pages: {a.pages}  Sort: {a.sort}")
    print(f"Save: {save_dir}")
    print(f"Filter: type=illust, page_count=1 only")
    print("=" * 50)

    # 1. Read cookie
    cookie = read_cookie()
    print("[auth] cookie loaded from config.ini")

    # 2. Search with pre-filter
    works = search_tag(a.tag, a.pages, a.sort, cookie)
    print(f"\n[search] {len(works)} single-page illustrations found")

    if not works:
        print("Nothing to download.")
        return

    # 3. Download each
    downloaded = 0
    skipped = 0
    failed = 0

    for i, w in enumerate(works, 1):
        # Check if already exists
        existing = list(Path(save_dir).glob(f"*-{w['id']}_*"))
        if existing:
            skipped += 1
            continue

        print(f"\n[{i}/{len(works)}] {w['id']} by {w['user_name']}")

        # Get original URL
        orig_url, _ = get_original_url(w["id"], cookie)
        if not orig_url:
            print("  SKIP: could not get original URL")
            failed += 1
            continue

        # Extract extension from URL
        ext = orig_url.rsplit(".", 1)[-1].split("?")[0]
        if ext not in ("jpg", "jpeg", "png", "gif"):
            ext = "jpg"

        filename = make_filename(w["user_id"], w["id"], ext)
        filepath = os.path.join(save_dir, filename)

        if download_image(orig_url, filepath, cookie):
            downloaded += 1
        else:
            failed += 1

        # Rate limit
        time.sleep(1.5)

    # 4. Safety clean
    print("\n" + "=" * 50)
    print("Safety clean ...")
    print("=" * 50)
    run_clean(save_dir, a.manga_threshold)

    print(f"\nDone! Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
