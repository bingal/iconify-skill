# Agent Guide for iconify-skill

This document provides the essential context an AI coding agent needs to work effectively on the `iconify-skill` project.

## Project Overview

`iconify-skill` is a Python CLI tool and agent skill for searching and retrieving SVG icons from [Iconify](https://iconify.design/) collections. It supports offline search via a bundled SQLite FTS5 index and online retrieval of individual SVGs from the Iconify API / GitHub raw JSON.

Key capabilities:
- **Offline search** across ~32,400 curated icons using SQLite FTS5, with automatic online fallback
- **Online SVG retrieval** with customizable size and color
- **Intent-based suggestions** via keyword mapping
- **Attribution reporting** for license compliance
- **System health checks** via the `doctor` command

The project is a pure-Python, stdlib-only package requiring Python >= 3.8. It is distributed via `setuptools` and exposes the CLI entry point `iconify`.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ |
| Packaging | `setuptools` (PEP 621 via `pyproject.toml`) |
| Search Engine | SQLite FTS5 (virtual table) |
| HTTP Client | `urllib.request` from stdlib |
| Testing | `pytest`, `pytest-cov` |
| CI/CD | GitHub Actions |

There are **no runtime dependencies outside the Python standard library**.

## Project Structure

```
iconify-skill/
├── pyproject.toml              # Package metadata, entry points, dev deps
├── pytest.ini                  # Test configuration
├── SKILL.md                    # Human/agent-facing skill documentation
├── AGENTS.md                   # This file
├── scripts/
│   ├── iconify_cli.py          # Main CLI: all commands, caching, SVG assembly
│   ├── build_index.py          # Standalone SQLite FTS5 index builder
│   ├── doctor.py               # Detailed system health checker
│   └── update_bundled_data.py  # Maintenance script to rebuild bundled data/
├── data/
│   ├── icons.db                # Bundled SQLite search index (offline use)
│   ├── collections.json        # Bundled collection metadata
│   └── icons.zip               # Archive of bundled data for distribution
├── assets/
│   ├── curated_sets.txt        # Preferred MIT/ISC-licensed icon set prefixes
│   └── intent_keywords.json    # Natural-language intent -> icon ID mapping
├── references/
│   ├── REFERENCE.md            # Deep-dive architecture, cache strategy, API docs
│   └── LICENSES_AND_ATTRIBUTION.md  # License requirements per collection
├── tests/
│   └── test_iconify.py         # pytest suite
└── .github/workflows/
    └── update-icons.yml        # (Removed) Previously scheduled weekly updates
```

### Module Responsibilities

- **`scripts/iconify_cli.py`** (573 lines) — The primary module. Defines `main()`, argument parsers, and all command implementations:
  - `list_collections()` — lists icon sets with license info.
  - `search_icons()` / `search_index()` — offline FTS5 search with prefix filtering; falls back to Iconify online search API when local results are insufficient.
  - `get_svg()` — fetches raw JSON, resolves aliases, sanitizes SVG, and assembles output.
  - `suggest_icons()` — uses `assets/intent_keywords.json` to translate intent into search queries.
  - `show_attribution()` — prints license summaries.
  - `doctor()` — lightweight health check.
  - `build_index()` — builds the SQLite FTS5 index (also exposed as its own subcommand).
  - Shared utilities: `http_get()` (with MD5-based file cache), `get_cache_path()`, `ensure_cache_dir()`, `sanitize_svg()`, `resolve_aliases()`.

- **`scripts/build_index.py`** (270 lines) — Standalone index builder that can be run independently. Provides `build`, `optimize`, and `stats` subcommands. Imported by `iconify_cli.py` for the `build-index` CLI command.

- **`scripts/doctor.py`** (265 lines) — Extended health checker class (`Doctor`) with decorated check methods. Validates Python version, cache directory, network, API reachability, SQLite FTS5 support, index integrity, and script presence. Prints pass/fail summary and suggests fixes.

- **`scripts/update_bundled_data.py`** (283 lines) — Maintenance script for manual updates. By default indexes only the curated sets listed in `assets/curated_sets.txt` (~32K icons). Supports `--collections` to override. Fetches collections from the Iconify API, builds the SQLite index, saves metadata, creates `data/icons.zip`, and verifies bundle integrity.

## Build and Test Commands

### Running Tests

```bash
# Run the full test suite (verbose output is configured in pytest.ini)
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=scripts
```

**Note:** All tests pass from the project root. Subprocess-based tests use `Path(__file__).parent.parent / "scripts" / "..."` to resolve the correct script paths.

### Running the CLI

```bash
# Direct execution (recommended during development)
python scripts/iconify_cli.py <command> [args]

# After pip install (entry point defined in pyproject.toml)
iconify <command> [args]
```

### Common CLI Commands

```bash
# Health check
python scripts/iconify_cli.py doctor

# Build offline search index
python scripts/iconify_cli.py build-index --force

# Search icons (offline + online fallback)
python scripts/iconify_cli.py search "home" --limit 5 --prefixes mdi,lucide

# Fetch SVG (requires network)
python scripts/iconify_cli.py get mdi:home --size 24 --color "#3B82F6"

# Suggest icons for an intent
python scripts/iconify_cli.py suggest "user profile page"

# Show attribution
python scripts/iconify_cli.py attribution --prefixes mdi,heroicons
```

### Updating Bundled Data

```bash
# Rebuild the bundled index and zip archive for offline distribution
python scripts/update_bundled_data.py

# Filter to specific collections
python scripts/update_bundled_data.py --collections mdi,bi,lucide,heroicons

# Verify existing bundle without rebuilding
python scripts/update_bundled_data.py --verify
```

## Code Style Guidelines

- **Follow existing conventions**: The codebase uses PEP 8 style with 4-space indentation.
- **Docstrings**: Use triple-quoted docstrings for modules and public functions. Docstrings often include usage examples.
- **Type hints**: Minimal usage; some functions use `-> dict`, `-> Path`, `-> bool`. Do not introduce heavy typing unless the surrounding code already does.
- **String formatting**: Mix of f-strings and `.format()`. Prefer f-strings for new code unless consistency with a specific module dictates otherwise.
- **Error handling**: Use `try/except` blocks around network and JSON parsing. Print warnings to `stderr` via `print(..., file=sys.stderr)`. Return non-zero exit codes on failure.
- **Constants**: Module-level uppercase constants (e.g., `CACHE_DIR`, `ICONIFY_API`) are defined near the top of each script.
- **No external imports**: Do not add third-party dependencies. If you need HTTP, use `urllib.request`. If you need parsing, use `json` or `re` from stdlib.

## Testing Instructions

- Tests live in `tests/test_iconify.py` and are organized by `pytest` classes (`TestSanitization`, `TestCache`, `TestSVGAssembly`, etc.).
- The test runner is configured via `pytest.ini`:
  - `testpaths = tests`
  - `addopts = -v`
- Some tests import `iconify_cli` via `sys.path.insert` to reach the `scripts/` directory.
- When adding new features, add corresponding tests in `tests/test_iconify.py`.
- Subprocess-based tests should use the correct relative path from the project root (e.g., `scripts/build_index.py`) rather than assuming the CWD is `scripts/`.

## Runtime Architecture

### Data Flow

```
User Input -> argparse -> Command Function -> Iconify API / SQLite Index -> Cache -> SVG/Text Output
```

### Caching Strategy

- **Location**: `~/.cache/iconify-skill/` (override with `ICONIFY_CACHE_DIR` env var).
- **Keys**: MD5 hashes of URLs with `.json` suffix.
- **Behavior**: `http_get()` checks the local cache first. On network failure, it falls back to stale cache. There is no automatic TTL.
- **Cached files**:
  - Collection metadata (`collections.json`)
  - Individual prefix JSON (`{md5}.json`)
  - Search index (`icons.db`)
  - Index metadata (`index_meta.json`)

### Search Index (SQLite FTS5)

Two tables are maintained:

```sql
CREATE VIRTUAL TABLE icons_fts USING fts5(prefix, name, full_id, tokens);
CREATE TABLE icons (oid INTEGER PRIMARY KEY, prefix TEXT, name TEXT, full_id TEXT, aliases TEXT, license TEXT);
```

- `icons_fts` powers the BM25-ranked search.
- `icons` stores denormalized metadata (aliases, license).
- Queries use automatic wildcard insertion: `*home*` for partial matching.

### SVG Assembly & Security

1. Fetch raw collection JSON from GitHub.
2. Resolve icon aliases (follow `parent` chains).
3. **Sanitize** the SVG body:
   - Reject `<script>` tags.
   - Reject `onload=` event handlers.
   - Reject external `href` links.
4. Wrap in `<svg xmlns="http://www.w3.org/2000/svg" viewBox="..." width="..." height="...">`.
5. If a custom color is provided (and not `currentColor`), wrap paths in `<g fill="{color}">`.
6. Append HTML comments with attribution (`<!-- Icon: prefix:name -->`, `<!-- License: ... -->`).

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error / no results / invalid arguments |
| 2 | Network error (`get` command) |
| 3 | Database error (offline mode) |

## Deployment & Automation

- **GitHub Actions**: The weekly scheduled workflow has been removed to avoid bloating the repository with large data updates. Manual updates can still be run locally with `scripts/update_bundled_data.py`.
- **Entry point**: `pyproject.toml` registers `iconify = iconify_cli:main`. Note that `iconify_cli.py` lives in `scripts/`, not a top-level package directory.
- **Distribution**: The `data/` directory contains pre-built offline assets (`icons.db`, `collections.json`, `icons.zip`) for the curated icon sets only. This keeps the skill lightweight while preserving offline search capability.

## Security Considerations

- **SVG sanitization is mandatory**: Any code path that outputs SVG must pass through `sanitize_svg()` to prevent injection of scripts or external references.
- **No secrets**: The project does not use API keys or credentials. It relies on public Iconify/GitHub endpoints.
- **User-controlled input**: The `get` and `search` commands accept user input. SQL queries in `search_index()` use parameterized statements; however, the `prefixes` list is interpolated into the SQL string via `",".join(f"'{p}'" for p in prefixes)`. If modifying this code, avoid introducing SQL injection by sanitizing prefix values.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ICONIFY_CACHE_DIR` | `~/.cache/iconify-skill/` | Local cache directory |

## Useful References

- `references/REFERENCE.md` — Detailed architecture, cache invalidation policy, collection structure, performance notes, and integration examples.
- `references/LICENSES_AND_ATTRIBUTION.md` — License breakdowns per icon collection and best practices for attribution.
- `SKILL.md` — Quickstart and common usage examples for end users.
