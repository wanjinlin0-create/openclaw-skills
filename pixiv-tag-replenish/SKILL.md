---
name: pixiv-tag-replenish
description: >
  Replenish Pixiv image collections by tag. Searches via Pixiv Ajax API with
  type=illust pre-filter (no manga, no ugoira, single-page only), then downloads
  originals directly. Includes safety clean step. Also usable standalone to clean
  any existing Pixiv download folder.
  Triggers: "补充标签", "下载标签", "补库存", "下载JK/眼镜/黑丝/白丝/萝莉/泳装",
  "整理标签文件夹", "清理漫画", "去重套图", "Pixiv下载".
---

# Pixiv Tag Replenish (v2)

Search Pixiv by tag with API pre-filter -> download single-page illustrations only -> NAS.

## How It Works

1. Read cookie from PixivUtil2 `config.ini`
2. Call Pixiv Ajax search API with `type=illust` (excludes manga and ugoira at source)
3. Filter results to `page_count == 1` only (single illustrations)
4. Download originals via requests (with Referer header)
5. Skip files that already exist in target folder
6. Run `clean.py` as safety net

## Prerequisites

- **PixivUtil2 config.ini** with valid cookie (for authentication)
- **NAS** at `\\GBWSSforNAS\Download\pixiv\05_标签合集\`

## Full Pipeline

```bash
python scripts/replenish.py <tag> [--pages 3] [--sort popular_d]
```

```bash
python scripts/replenish.py 水着 --pages 3
python scripts/replenish.py 眼鏡 --pages 5
python scripts/replenish.py JK --pages 3 --sort date_d
```

## Clean Only

```bash
python scripts/clean.py <folder_path>
python scripts/clean.py "\\GBWSSforNAS\Download\pixiv\05_标签合集\眼镜" --dry-run
```

## Cleaning Rules (safety net)

| Rule | Condition | Action |
|------|-----------|--------|
| Flatten | Files in subdirs | Move to root |
| Manga delete | Work has 4+ pages | Delete ALL pages |
| Page dedup | Work has 2-3 pages | Keep page 0 only |

Note: Same artist with multiple works is NOT deduplicated.

## Tag to Folder Mapping

Edit `TAG_FOLDERS` in `scripts/replenish.py`:

| Pixiv Tag | NAS Folder |
|-----------|------------|
| 眼鏡 / めがね | 眼镜 |
| 黒タイツ / 黒スト | 黑丝 |
| 白タイツ / 白スト | 白丝 |
| ロリ | 萝莉 |
| JK | JK |
| 水着 / swimsuit | 泳装 |

Unmapped tags use the tag name as folder name.

## Filename Format

`{member_id}-{image_id}_.{ext}` (single-page, no page index)

## Tested Results

| Tag | Search | Filtered | Downloaded | Waste |
|-----|--------|----------|------------|-------|
| 雌小鬼 | 60 | 24 | 8 (16 existed) | 0% |
| 水着 | 180 | 131 | 131 | 0% |

## PixivUtil2 Reference

See [references/pixivutil2-reference.md](references/pixivutil2-reference.md).
