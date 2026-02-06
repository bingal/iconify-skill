# Licenses and Attribution

## Overview

Iconify aggregates icons from many different sources, each with their own license. This document outlines the major licenses and attribution requirements.

## License Types

### MIT License
**Common in:** Material Design Icons, Bootstrap Icons, Heroicons, Tabler Icons

**Requirements:**
- Include license notice in distribution
- Permissive for commercial use

### SIL OFL 1.1 (Open Font License)
**Common in:** Font Awesome (free icons)

**Requirements:**
- Cannot sell the icons themselves
- Must include license notice
- Can embed in software/webpages

### Apache 2.0
**Common in:** Some open source icon sets

**Requirements:**
- Include license notice
- State changes made
- Patent license grant

### ISC License
**Common in:** Lucide

**Requirements:**
- Simple permissive license
- Include license notice

## Popular Collections

### Material Design Icons (mdi)
- **License:** MIT
- **Source:** https://github.com/Templarian/MaterialDesign
- **Attribution:** Not required (MIT)

### Font Awesome Free (fa)
- **License:** SIL OFL 1.1
- **Source:** https://fontawesome.com
- **Attribution:** "Font Awesome Free 6.5.1 by @fontawesome"

### Bootstrap Icons (bi)
- **License:** MIT
- **Source:** https://github.com/twbs/icons
- **Attribution:** Not required (MIT)

### Lucide (lucide)
- **License:** ISC
- **Source:** https://github.com/lucide-icons/lucide
- **Attribution:** Not required (ISC)

### Heroicons (heroicons)
- **License:** MIT
- **Source:** https://github.com/tailwindlabs/heroicons
- **Attribution:** Not required (MIT)

### Tabler Icons (tabler)
- **License:** MIT
- **Source:** https://github.com/tabler/tabler-icons
- **Attribution:** Not required (MIT)

### Feather (feather)
- **License:** MIT
- **Source:** https://github.com/feathericons/feather
- **Attribution:** Not required (MIT)

## Attribution Generator

Use the CLI to generate attribution notices:

```bash
# Attribution for all collections
iconify attribution

# Attribution for specific collections
iconify attribution --prefixes mdi,fa,heroicons
```

### Sample Attribution Output
```markdown
# Icon Attribution Summary

## mdi
License: MIT
URL: https://github.com/Templarian/MaterialDesign

## fa
License: SIL OFL 1.1
URL: https://fontawesome.com
Requirements: "Font Awesome Free" must be credited

## heroicons
License: MIT
URL: https://github.com/tailwindlabs/heroicons
```

## Generating Attribution in Code

```python
import subprocess

def generate_notice(prefixes):
    """Generate attribution notice for used icons."""
    result = subprocess.run(
        ["iconify", "attribution", "--prefixes", ",".join(prefixes)],
        capture_output=True, text=True
    )
    return result.stdout

# For a project using mdi and heroicons
notice = generate_notice(["mdi", "heroicons"])
print(notice)
```

## Best Practices

1. **Check individual icons** - Some icons in a collection may have different licenses
2. **Keep attribution notices** - Include in your project's documentation
3. **Update regularly** - Licenses may change as icon sets evolve
4. **Use curated sets** - For consistent licensing, use only MIT/ISC licensed sets

## Safe Sets (MIT/ISC only)

For projects requiring simple attribution, use these sets:

```
mdi, bi, lucide, heroicons, tabler, feather, ph, radix-icons
```

## Commercial Use

| Collection | Commercial Use | Attribution Required |
|------------|----------------|----------------------|
| mdi | Yes | No |
| fa (Free) | Yes | Yes (credit Font Awesome) |
| bi | Yes | No |
| lucide | Yes | No |
| heroicons | Yes | No |
| tabler | Yes | No |
| fa-brands | Limited | Yes |

## Resources

- [Choose a License - GitHub](https://choosealicense.com)
- [SIL OFL FAQ](https://scripts.sil.org/OFL-FAQ)
- [Open Source Initiative](https://opensource.org/licenses)
