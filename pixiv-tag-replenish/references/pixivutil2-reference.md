# PixivUtil2 Quick Reference

## Batch Mode

```bash
python PixivUtil2.py -s b -x -c config.ini
```

## batch_job.json

```json
{
  "jobs": {
    "tag_search": {
      "job_type": "3",
      "tags": "JK",
      "start_page": 1,
      "end_page": 3,
      "sort_order": "popular_d",
      "enabled": true
    }
  }
}
```

### sort_order
- `popular_d` — by popularity (premium only, recommended)
- `date_d` — by date descending
- `date` — by date ascending

## config.ini Critical Settings

### Flat output (no nested folders)
```ini
[Filename]
filenameFormat = %member_id%-%image_id%_%page_index%
filenameMangaFormat = %member_id%-%image_id%_%page_index%
createMangaDir = False
useTagsAsDir = False

[Settings]
rootDirectory = \\NAS\path\to\tag_folder
```

### Common issues
- **Duplicate keys** in config.ini cause parse errors — the replenish script auto-deduplicates
- **SSL EOF errors** are frequent — PixivUtil2 retries automatically (3 retries default)
- **Cookie expiry** — re-export from browser if login fails

## Output Filename Format

`{member_id}-{image_id}_{page_index}.{ext}`

| Example | Meaning |
|---------|---------|
| `9016-86352661_0.jpg` | Artist 9016, work 86352661, page 0 |
| `6525386-68079957_.jpg` | Single-page work (no page index) |
