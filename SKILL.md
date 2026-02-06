---
name: iconify-svg
description: Search and retrieve SVG icons from Iconify collections (offline-capable)
category: developer-tools
keywords:
  - icon
  - svg
  - iconify
  - graphics
  - ui
  - icons
agent_timeout: 60
metadata:
  {
    "openclaw":
      {
        "emoji": "🎨",
        "requires": { "bins": ["python3"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "pip",
              "label": "Install via pip (skill/scripts/)",
              "command": "python3 $SKILL_DIR/scripts/iconify_cli.py --help"
            },
            {
              "id": "clone",
              "kind": "clone",
              "label": "Clone skill to skills directory",
              "url": "https://github.com/bingal/iconify-skill.git"
            },
          ],
      },
  }
---

# Iconify SVG Skill

Search and retrieve production-ready SVG icons from the Iconify ecosystem.

## Features

- **32,000+ icons** from 9 popular collections (Material Design, Phosphor, Tabler, etc.)
- **Offline support** - bundled data enables searching without internet
- **Full-text search** - find icons by name, aliases, or keywords
- **SVG generation** - get clean, production-ready SVG code
- **License tracking** - automatic attribution for each icon

## When to Use

Use this skill when you need to:
- Find appropriate icons for a UI component or feature
- Generate SVG code for embedding in applications
- Check icon licensing and attribution requirements
- Search icon collections using keywords or natural language

## Quickstart

```bash
# List all available icon collections
iconify list-collections

# Search for icons by keyword
iconify search "arrow right" --limit 10

# Get SVG code for a specific icon
iconify get mdi:arrow-right --size 24 --color "#3B82F6"

# Get attribution info
iconify attribution --prefixes mdi

# Check system health (including offline capability)
iconify doctor
```

## Core Commands

| Command | Description |
|---------|-------------|
| `list-collections` | Show all available icon sets |
| `search <query>` | Find icons matching query |
| `get <prefix:name>` | Get SVG for specific icon |
| `suggest "<intent>"` | Suggest icons based on intent |
| `attribution` | Show license/attribution info |
| `doctor` | Check system health |
| `build-index` | Build/update search index |

## Examples

### Search for icons
```bash
iconify search "close button" --limit 5
# Output: mdi:close, bi:x-lg, lucide:x, tabler:x, ...
```

### Get an SVG icon with custom styling
```bash
iconify get mdi:check --size 32 --color "#10B981"
# Output: <svg ...>...</svg>
```

### Find icons for a feature
```bash
iconify suggest "user profile page"
# Suggests: account, user, user-circle, user-add icons
```

### Filter by specific icon set
```bash
iconify search "home" --prefixes lucide,heroicons
# Only search in Lucide and Heroicons collections
```

## Bundled Icon Collections

The skill includes **32,206 icons** from these collections:

| Collection | Icons | License |
|------------|-------|---------|
| mdi (Material Design) | 7,638 | MIT |
| ph (Phosphor) | 9,161 | MIT |
| tabler (Tabler Icons) | 6,034 | MIT |
| simple-icons | 3,663 | CC0 1.0 |
| lucide | 1,710 | MIT |
| bi (Bootstrap) | 2,084 | MIT |
| heroicons | 1,288 | MIT |
| feather | 286 | MIT |
| radix-icons | 342 | MIT |

## Updating Bundled Data

To update the bundled icon data:

```bash
# Update with all collections
python scripts/update_bundled_data.py

# Update with specific collections
python scripts/update_bundled_data.py --collections mdi,bi,lucide
```

## Output Format

### SVG Output
```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 24 24"
     width="24" height="24">
  <path fill="#3B82F6" d="..."/>
</svg>

<!-- Icon: mdi:check -->
<!-- License: MIT -->
```

## Compliance Notes

- Iconify collections have varying licenses (MIT, SIL OFL, Apache 2.0, etc.)
- Most bundled icons use permissive MIT/CC0 licenses
- Some brand icons (simple-icons) may have trademark restrictions
- Check `iconify attribution --prefixes <collection>` for details
- Always verify the license for your specific use case

## Performance

- **Search** uses SQLite FTS5 full-text search (instant)
- **Get icon** fetches from network (icons API)
- Offline mode: search works without internet, get requires network
- Cache: API responses cached in `~/.cache/iconify-svg/`

## Requirements

- Python 3.8+
- SQLite (usually bundled with Python)
- Internet connection (for fetching SVG data)
