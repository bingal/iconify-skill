---
name: iconify-skill
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
        "offline_capable": true,
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

## For AI Agents

### Discovery
1. Read `SKILL.md` in skill directory
2. Check prerequisites: `python3` required

### Verification
```bash
python3 $SKILL_DIR/scripts/iconify_cli.py doctor
```

### Command Interface
```bash
python3 $SKILL_DIR/scripts/iconify_cli.py <command> [arguments]
```

### Available Commands
- `list-collections` - List icon sets
- `search <query>` - Search icons (offline)
- `get <prefix:name>` - Get SVG (requires network)
- `suggest "<intent>"` - Suggest icons for intent
- `attribution` - Show license info
- `doctor` - System health check

## Usage Examples

```bash
# Search icons (offline)
python3 $SKILL_DIR/scripts/iconify_cli.py search "close button" --limit 5

# Get SVG with custom styling
python3 $SKILL_DIR/scripts/iconify_cli.py get mdi:home --size 24 --color "#3B82F6"

# Suggest icons for a feature
python3 $SKILL_DIR/scripts/iconify_cli.py suggest "user profile page"

# Filter by collection
python3 $SKILL_DIR/scripts/iconify_cli.py search "home" --prefixes lucide,heroicons
```

## Bundled Collections (32K icons)

mdi, ph, tabler, simple-icons, lucide, bi, heroicons, feather, radix-icons

## Output Format

### Exit Codes
- `0` - Success
- `1` - No icons found / invalid arguments
- `2` - Network error (get command)
- `3` - Database error (offline mode)

### SVG Output
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#3B82F6" d="..."/>
</svg>
<!-- Icon: mdi:check -->
<!-- License: MIT -->
```

## Offline Capability

- **Search**: Works offline (bundled SQLite FTS5 index)
- **Get**: Requires internet (fetches SVG from Iconify API)
- Use `doctor` command to verify offline data availability
