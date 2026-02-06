# Iconify SVG Skill

Search and retrieve production-ready SVG icons from Iconify collections. Includes **32,000+ icons** bundled for offline search capability.

## Quick Start

```bash
# Install the CLI
cd iconify-skill
pip install -e .

# List available icon collections
iconify list-collections

# Search for icons (works offline!)
iconify search "arrow right" --limit 10

# Get SVG for an icon (requires internet)
iconify get mdi:arrow-right --size 24 --color "#3B82F6"
```

## For AI Agents

This skill is designed for AI agents to quickly find and use icons:

```markdown
# SKILL.md
Use iconify CLI:
- `iconify search <query>` - Find icons (offline)
- `iconify get <prefix:name>` - Get SVG code (online)
- `iconify suggest "<intent>"` - Get suggestions (offline)
- `iconify doctor` - Check system health
```

## Features

- ✓ **32,206 icons** from 9 popular collections (bundled)
- ✓ **Offline search** - find icons without internet
- ✓ Production-ready SVG output with customizable size/color
- ✓ Automatic license and attribution tracking
- ✓ SQLite FTS5 full-text search (instant results)
- ✓ Fast local caching for network requests

## Bundled Collections

| Collection | Icons | License |
|------------|-------|---------|
| mdi (Material Design) | 7,638 | MIT/Apache 2.0 |
| ph (Phosphor) | 9,161 | MIT |
| tabler | 6,034 | MIT |
| simple-icons | 3,663 | CC0 1.0 |
| lucide | 1,710 | ISC/MIT |
| bi (Bootstrap) | 2,084 | MIT |
| heroicons | 1,288 | MIT |
| feather | 286 | MIT |
| radix-icons | 342 | MIT |

**Total: 32,206 icons**

## Project Structure

```
iconify-skill/
├── SKILL.md              # Agent skill definition
├── data/                 # Bundled icon data (offline support)
│   ├── icons.db          # SQLite FTS5 search index
│   ├── collections.json  # Collection metadata
│   └── icons.zip         # Archive for distribution
├── scripts/
│   ├── iconify_cli.py    # Main CLI (16KB)
│   ├── build_index.py    # Build search index
│   ├── doctor.py         # Health checks
│   └── update_bundled_data.py  # Update bundled data
├── references/
│   ├── REFERENCE.md      # Technical docs
│   └── LICENSES_AND_ATTRIBUTION.md
├── assets/
│   ├── curated_sets.txt  # Preferred icon sets
│   └── intent_keywords.json
└── tests/
    └── test_iconify.py
```

## Commands

| Command | Description | Offline |
|---------|-------------|---------|
| `list-collections` | List all icon collections | ✓ |
| `search <query>` | Search icons by keyword | ✓ |
| `get <prefix:name>` | Get SVG code | ✗ |
| `suggest "<intent>"` | Suggest icons for intent | ✓ |
| `attribution` | Show license info | ✓ |
| `doctor` | System health check | ✓ |
| `build-index` | Build/update search index | ✗ |

## Examples

### Search for user icons
```bash
iconify search "user profile" --limit 5
# mdi:account, lucide:user, heroicons:user, ...
```

### Get a colored icon
```bash
iconify get bi:github --size 32 --color "#333333"
```

### Filter by specific collection
```bash
iconify search "home" --prefixes lucide,heroicons
```

### Attribution info
```bash
iconify attribution --prefixes mdi,bi,lucide
```

## Updating Bundled Data

To update the bundled icon data:

```bash
# Update with all collections
python scripts/update_bundled_data.py

# Update with specific collections
python scripts/update_bundled_data.py --collections mdi,bi,lucide

# Verify the bundle
python scripts/update_bundled_data.py --verify
```

## Development

```bash
# Run tests
pytest tests/

# Build search index (cache)
python scripts/build_index.py build

# Build bundled data (offline)
python scripts/build_index.py build --bundle --prefixes mdi,bi,lucide

# Check system health
python scripts/doctor.py
```

## License

MIT License - see LICENSE file.

Icon collections have their own licenses. See `references/LICENSES_AND_ATTRIBUTION.md` for details.
