# Iconify SVG Reference

## Architecture

### Components

```
iconify-svg/
├── scripts/
│   ├── iconify_cli.py      # Main CLI entry point
│   ├── build_index.py      # Build SQLite FTS index
│   └── doctor.py           # System health checks
├── references/
│   ├── REFERENCE.md        # This file
│   └── LICENSES_AND_ATTRIBUTION.md
├── assets/
│   ├── curated_sets.txt    # Preferred icon sets
│   └── intent_keywords.json # Intent to keyword mapping
└── SKILL.md               # Agent skill definition
```

### Data Flow

```
CLI Input → Iconify API → Cache → Process → SVG Output
                 ↓
            SQLite Index (optional, for fast search)
```

## Iconify API

The CLI uses the Iconify API at `https://api.iconify.design`:

- `/collections.json` - List all available collections
- `/{prefix}.json` - Get all icons in a collection
- `/{prefix}/{name}.svg` - Get single SVG (alternative)

## Caching Strategy

### Cache Location
- Default: `~/.cache/iconify-svg/`
- Override: Set `ICONIFY_CACHE_DIR` environment variable

### Cached Files
- `collections.json` - Collection metadata
- `{prefix}.json` - Individual collection data
- `icons.db` - SQLite FTS5 search index
- `index_meta.json` - Index build metadata
- `intent_keywords.json` - User-defined intent mappings

### Cache Invalidation
- Collections cache: Never expires (stable API)
- Collection data: Freshen on fetch errors
- Index: Manual rebuild with `--force`

## Icon Resolution

### Prefix:Name Format
Icons are referenced as `{prefix}:{name}`:
- `mdi:home` - Material Design Icons, "home" icon
- `fa:user` - Font Awesome, "user" icon

### Aliases
Many icons have aliases (alternative names):
```
mdi:arrow-right
  └── alias: mdi:arrow-right-bold
```

The CLI automatically resolves aliases to the parent icon.

## SVG Assembly

### Basic Assembly
```python
body = icon["body"]  # SVG path(s)
width = icon.get("width", 24)
height = icon.get("height", 24)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {width} {height}"
     width="{size}" height="{size}">
  {body}
</svg>'''
```

### Color Handling
- Default: `currentColor` (inherits from CSS)
- Custom: Wrapped in `<g fill="{color}">` tag

### Sanitization
The CLI rejects icons containing:
- `<script>` tags
- `onload=` handlers
- External `href` links

## Search Index

### Building the Index
```bash
iconify build-index  # Creates ~/.cache/iconify-svg/icons.db
iconify build-index --force  # Rebuild existing index
```

### Index Schema
```sql
CREATE VIRTUAL TABLE icons_fts USING fts5(
    prefix, name, full_id, tokens
)

CREATE TABLE icons (
    oid INTEGER PRIMARY KEY,
    prefix TEXT,
    name TEXT,
    full_id TEXT,
    aliases TEXT,
    license TEXT
)
```

### Querying
```python
# FTS5 query with wildcards
cursor.execute(
    "SELECT prefix, name FROM icons_fts WHERE icons_fts MATCH ?",
    ("home user",)  # Wildcards added automatically
)
```

## Collections

### Popular Collections

| Prefix | Name | Icons | License |
|--------|------|-------|---------|
| mdi | Material Design Icons | 7000+ | MIT |
| fa | Font Awesome | 2000+ | SIL OFL 1.1 |
| bi | Bootstrap Icons | 1800+ | MIT |
| lucide | Lucide | 1000+ | ISC |
| heroicons | Heroicons | 600+ | MIT |
| tabler | Tabler Icons | 4000+ | MIT |

### Collection Info Structure
```json
{
  "prefix": "mdi",
  "name": "Material Design Icons",
  "total": 7294,
  "license": {
    "title": "MIT",
    "url": "https://github.com/Templarian/MaterialDesign/blob/master/LICENSE",
    "requirements": "Applies to icon set only"
  }
}
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Unknown prefix: foo" | Invalid collection prefix | Check with `list-collections` |
| "Icon not found: p:n" | Icon doesn't exist | Verify name spelling |
| Network timeout | API unreachable | Check internet connection |
| Index not found | Index not built | Run `build-index` |

### Exit Codes
- `0` - Success
- `1` - Error (check stderr)
- `2` - Invalid arguments

## Performance

### Typical Response Times
| Operation | Time (cached) | Time (cold) |
|-----------|---------------|-------------|
| list-collections | < 0.1s | < 1s |
| search (FTS) | < 0.1s | N/A |
| search (fallback) | < 1s | < 5s |
| get-svg | < 0.1s | < 0.5s |

### Memory Usage
- CLI: ~10-50MB (varies with cache size)
- Index: ~1MB per 100,000 icons

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ICONIFY_CACHE_DIR` | `~/.cache/iconify-svg/` | Cache directory |
| `ICONIFY_API_URL` | `https://api.iconify.design` | API endpoint |

## Integration Examples

### In Python Code
```python
import subprocess

# Get SVG
result = subprocess.run(
    ["iconify", "get", "mdi:home", "--size", "24"],
    capture_output=True, text=True
)
svg = result.stdout

# Parse for embedding
from xml.etree import ElementTree as ET
root = ET.fromstring(svg)
```

### In Shell Scripts
```bash
#!/bin/bash
# Get icon and save to file
iconify get mdi:github --size 32 --color "#333" > github.svg
```
