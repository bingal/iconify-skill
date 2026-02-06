# Iconify SVG Skill

Search and retrieve production-ready SVG icons from Iconify collections. **32,000+ icons** bundled for offline search.

## For AI Agents

This is an OpenClaw/Claude agent skill. Agents should read `SKILL.md` for usage instructions.

## Installation

```bash
# Clone to your OpenClaw skills directory
cd ~/.openclaw/skills/
git clone https://github.com/bingal/iconify-skill.git

# Or copy the entire directory
cp -r /path/to/iconify-skill ~/.openclaw/skills/
```

## CLI Usage

```bash
cd iconify-skill

# Search icons (offline)
python3 scripts/iconify_cli.py search "settings" --limit 5

# Get SVG
python3 scripts/iconify_cli.py get mdi:check --size 24 --color "#10B981"

# System check
python3 scripts/iconify_cli.py doctor
```

## Update Bundled Data

```bash
# Update with all collections
python3 scripts/update_bundled_data.py

# Update with specific collections
python3 scripts/update_bundled_data.py --collections mdi,bi,lucide
```

## Bundled Collections

| Collection | Icons | License |
|------------|-------|---------|
| mdi | 7,638 | MIT/Apache 2.0 |
| ph | 9,161 | MIT |
| tabler | 6,034 | MIT |
| simple-icons | 3,663 | CC0 1.0 |
| lucide | 1,710 | ISC/MIT |
| bi | 2,084 | MIT |
| heroicons | 1,288 | MIT |
| feather | 286 | MIT |
| radix-icons | 342 | MIT |

**Total: 32,206 icons**

## License

MIT License - see LICENSE file.

Icon collections have their own licenses. See `references/LICENSES_AND_ATTRIBUTION.md`.
