---
name: iconify-svg
description: Find and generate SVG icons from Iconify collections. Search 32K+ icons offline, get production-ready SVG code with size/color customization.
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
              "id": "clone",
              "kind": "clone",
              "label": "Clone to skills directory",
              "url": "https://github.com/bingal/iconify-skill.git"
            },
          ],
      },
  }
---

# Iconify SVG

Search and retrieve production-ready SVG icons from Iconify collections.

## Usage

Run commands from the skill directory:

```bash
cd $SKILL_DIR
python3 scripts/iconify_cli.py <command> [options]
```

## Commands

| Command | Description |
|---------|-------------|
| `list-collections` | List available icon sets |
| `search <query>` | Search icons by keyword |
| `get <prefix:name>` | Get SVG for specific icon |
| `suggest "<intent>"` | Suggest icons for intent |
| `attribution` | Show license/attribution info |
| `doctor` | Check system health |

## Examples

```bash
# Search for icons (works offline)
python3 scripts/iconify_cli.py search "close button" --limit 5

# Get SVG with custom size/color
python3 scripts/iconify_cli.py get mdi:home --size 24 --color "#3B82F6"

# Find icons for a feature
python3 scripts/iconify_cli.py suggest "user profile page"

# Filter by specific collection
python3 scripts/iconify_cli.py search "home" --prefixes lucide,heroicons
```

## Bundled Collections (32K icons)

mdi, ph, tabler, simple-icons, lucide, bi, heroicons, feather, radix-icons

## Notes

- **Search**: Works offline (uses bundled FTS5 index)
- **Get**: Requires internet (fetches from Iconify API)
- Output includes license attribution comments
