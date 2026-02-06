#!/usr/bin/env python3
"""
Iconify SVG CLI - Search and retrieve SVG icons from Iconify collections.

Usage:
    iconify list-collections          # List available icon collections
    iconify search <query> [--limit N] [--prefixes p1,p2]  # Search icons
    iconify get <prefix:name> [--size N] [--color #hex]    # Get SVG
    iconify suggest "<intent text>"   # Suggest icons for intent
    iconify attribution [--prefixes p1,p2]  # Show attribution
    iconify doctor                    # Check system health
    iconify build-index [--force]     # Build search index
"""

import argparse
import json
import os
import sys
import hashlib
import re
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from functools import lru_cache
from datetime import datetime
import sqlite3

CACHE_DIR = Path(os.environ.get("ICONIFY_CACHE_DIR", Path.home() / ".cache" / "iconify-skill"))
# Iconify raw JSON from GitHub (most reliable)
ICONIFY_API = "https://api.iconify.design"
GITHUB_RAW = "https://raw.githubusercontent.com/iconify/icon-sets/master/json"

# Bundled data paths (for offline use)
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent  # iconify-skill directory
BUNDLE_DATA_DIR = SKILL_DIR / "data"
BUNDLE_INDEX = BUNDLE_DATA_DIR / "icons.db"
BUNDLE_METADATA = BUNDLE_DATA_DIR / "collections.json"
BUNDLE_ZIP = BUNDLE_DATA_DIR / "icons.zip"

# API endpoints
COLLECTIONS_URL = f"{ICONIFY_API}/collections"
GITHUB_COLLECTION_URL = f"{GITHUB_RAW}/"

# Version
__version__ = "1.0.0"


def ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def get_cache_path(key: str) -> Path:
    """Get cache file path for a key."""
    return ensure_cache_dir() / key


def http_get(url: str, timeout: float = 30.0) -> dict:
    """Fetch JSON from URL with caching."""
    cache_key = hashlib.md5(url.encode()).hexdigest() + ".json"
    cache_path = get_cache_path(cache_key)

    # Return cached if exists
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass  # Invalid cache, re-fetch

    # Fetch from network
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": f"iconify-skill/{__version__}"})
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            # Cache it
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            return data
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        # Try to return cached version even if expired
        if cache_path.exists():
            with open(cache_path) as f:
                return json.load(f)
        raise RuntimeError(f"Failed to fetch {url}: {e}")


def load_collections() -> dict:
    """Load available collections."""
    # Try bundled data first
    if BUNDLE_METADATA.exists():
        try:
            with open(BUNDLE_METADATA) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Fallback to network
    return http_get(COLLECTIONS_URL)


def has_bundled_index() -> bool:
    """Check if bundled index exists and is valid."""
    if not BUNDLE_INDEX.exists():
        return False
    try:
        conn = sqlite3.connect(str(BUNDLE_INDEX))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM icons")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def get_prefix_json(prefix: str) -> dict:
    """Get icon data for a specific prefix from GitHub raw JSON."""
    url = f"{GITHUB_COLLECTION_URL}/{prefix}.json"
    return http_get(url)


def list_collections():
    """List all available collections."""
    collections = load_collections()
    print(f"{'Prefix':<20} {'Total Icons':<12} {'License'}")
    print("-" * 70)
    for prefix, info in sorted(collections.items()):
        total = info.get("total", "?")
        license_info = info.get("license", {}).get("title", "Unknown")
        print(f"{prefix:<20} {total:<12} {license_info}")


def search_icons(query: str, limit: int = 20, prefixes: list = None):
    """Search for icons matching query."""
    # Priority: bundled index > cache index > network fallback
    index_path = None
    
    # Check bundled index first
    if has_bundled_index():
        index_path = BUNDLE_INDEX
    elif get_cache_path("icons.db").exists():
        index_path = get_cache_path("icons.db")
    
    if index_path:
        results = search_index(query, limit, prefixes, index_path)
        for prefix, name, score in results:
            print(f"{prefix}:{name} (score: {score})")
        return

    # Fallback: search through loaded collections (slow!)
    print("Warning: No search index available, falling back to network search...")
    collections = load_collections()
    results = []
    query_lower = query.lower()

    for prefix in collections:
        if prefixes and prefix not in prefixes:
            continue
        try:
            data = get_prefix_json(prefix)
            icons = data.get("icons", {})
            for name, icon in icons.items():
                # Search in name and aliases
                if (query_lower in name.lower() or
                    any(query_lower in a.lower() for a in icon.get("aliases", {}).keys())):
                    results.append((prefix, name))
                    if len(results) >= limit:
                        break
        except Exception:
            continue

    for prefix, name in results[:limit]:
        print(f"{prefix}:{name}")


def search_index(query: str, limit: int, prefixes: list = None, index_path: Path = None):
    """Search using SQLite FTS5 index."""
    if index_path is None:
        index_path = get_cache_path("icons.db")
    
    conn = sqlite3.connect(str(index_path))
    cursor = conn.cursor()

    sql = """
        SELECT prefix, name, bm25(icons_fts) as score
        FROM icons_fts
        WHERE icons_fts MATCH ? {}
        ORDER BY score
        LIMIT ?
    """.format("AND prefix IN ({})".format(",".join(f"'{p}'" for p in prefixes)) if prefixes else "")

    # Add wildcard for partial matching
    search_query = "*".join(query.split()) + "*"
    cursor.execute(sql, (search_query, limit))
    return cursor.fetchall()


def build_index(force: bool = False, bundle: bool = False, prefixes: list = None):
    """Build SQLite FTS5 index for fast searching."""
    if bundle:
        index_path = BUNDLE_INDEX
        ensure_data_dir()
    else:
        index_path = get_cache_path("icons.db")
    
    if index_path.exists() and not force:
        print("Index already exists. Use --force to rebuild.")
        return

    print("Building search index...")
    conn = sqlite3.connect(str(index_path))
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS icons_fts USING fts5(
            prefix, name, full_id, tokens
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS icons (
            oid INTEGER PRIMARY KEY,
            prefix TEXT,
            name TEXT,
            full_id TEXT,
            aliases TEXT,
            license TEXT
        )
    """)
    cursor.execute("DELETE FROM icons")
    cursor.execute("DELETE FROM icons_fts")

    # Index metadata
    meta_path = get_cache_path("index_meta.json")
    meta = {
        "build_time": datetime.now().isoformat(),
        "version": __version__
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # Load collections and index
    # Filter collections if prefixes specified
    if prefixes:
        collections = {k: v for k, v in collections.items() if k in prefixes}

    total = 0

    for prefix in collections:
        try:
            data = get_prefix_json(prefix)
            icons = data.get("icons", {})
            for name, icon in icons.items():
                full_id = f"{prefix}:{name}"
                aliases = " ".join(icon.get("aliases", {}).keys())
                license_info = data.get("license", {}).get("title", "Unknown")

                cursor.execute(
                    "INSERT INTO icons (prefix, name, full_id, aliases, license) VALUES (?, ?, ?, ?, ?)",
                    (prefix, name, full_id, aliases, license_info)
                )
                cursor.execute(
                    "INSERT INTO icons_fts (prefix, name, full_id, tokens) VALUES (?, ?, ?, ?)",
                    (prefix, name, full_id, f"{name} {aliases}")
                )
                total += 1
        except Exception as e:
            print(f"Warning: Failed to index {prefix}: {e}")
            continue

    conn.commit()
    conn.close()
    print(f"Indexed {total} icons from {len(collections)} collections.")

    # Save metadata to bundle if requested
    if bundle:
        # Get full collection list for metadata
        all_collections = http_get(COLLECTIONS_URL)
        filtered = {k: v for k, v in all_collections.items() if k in prefixes} if prefixes else all_collections
        
        with open(BUNDLE_METADATA, "w") as f:
            json.dump(filtered, f, indent=2)
        print(f"Saved metadata to {BUNDLE_METADATA}")


@lru_cache(maxsize=32)
def get_icon_data(prefix: str, name: str) -> dict:
    """Get icon data with caching."""
    data = get_prefix_json(prefix)
    return data.get("icons", {}).get(name, {})


def resolve_aliases(data: dict, name: str) -> dict:
    """Resolve icon aliases to get the actual icon data."""
    icons = data.get("icons", {})
    aliases = data.get("aliases", {})

    current = icons.get(name, {})
    while "parent" in current:
        parent_name = current["parent"]
        current = icons.get(parent_name, {})
    return current


def sanitize_svg(body: str) -> bool:
    """Check if SVG body is safe (no script, onload, or external links)."""
    body_lower = body.lower()
    if "<script" in body_lower:
        return False
    if "onload=" in body_lower:
        return False
    if re.search(r'href=["\']http', body_lower):
        return False
    return True


def get_svg(prefix: str, size: int = 24, color: str = None):
    """Get SVG string for an icon."""
    # Parse prefix:name format
    if ":" in prefix:
        prefix, name = prefix.split(":", 1)
    else:
        # Try to find in index
        conn = sqlite3.connect(str(get_cache_path("icons.db")))
        cursor = conn.cursor()
        cursor.execute("SELECT full_id FROM icons WHERE prefix = ? LIMIT 1", (prefix,))
        result = cursor.fetchone()
        conn.close()
        if result:
            prefix, name = result[0].split(":", 1)
        else:
            print(f"Unknown prefix: {prefix}")
            return

    # Get icon data
    data = get_prefix_json(prefix)
    icon = resolve_aliases(data, name)

    if not icon:
        print(f"Icon not found: {prefix}:{name}")
        return

    body = icon.get("body", "")
    if not body:
        print(f"Empty icon body: {prefix}:{name}")
        return

    # Sanitize
    if not sanitize_svg(body):
        print("Icon contains unsafe elements, skipping.")
        return

    # Get dimensions
    width = icon.get("width", size)
    height = icon.get("height", size)

    # Build SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'viewBox="0 0 {width} {height}"',
        f'width="{size}" height="{size}">'
    ]

    if color and color != "currentColor":
        svg_parts.append(f'<g fill="{color}">')
        svg_parts.append(body)
        svg_parts.append('</g>')
    else:
        svg_parts.append(body)

    svg_parts.append('</svg>')

    svg = "\n".join(svg_parts)

    # Output SVG
    print(svg)

    # Output attribution
    license_info = data.get("license", {})
    print(f"\n<!-- Icon: {prefix}:{name} -->")
    print(f"<!-- License: {license_info.get('title', 'Unknown')} -->")
    if license_info.get("url"):
        print(f"<!-- License URL: {license_info['url']} -->")


def suggest_icons(intent: str):
    """Suggest icons based on intent description."""
    # Load intent keywords mapping
    keywords_path = get_cache_path("intent_keywords.json")
    if keywords_path.exists():
        with open(keywords_path) as f:
            intent_map = json.load(f)
    else:
        intent_map = {}

    # Try to match intent
    intent_lower = intent.lower()

    # Default keyword extraction
    keywords = re.findall(r'\b\w+\b', intent_lower)

    # Try to find matching query
    query = None
    for key, icons in intent_map.items():
        if key in intent_lower:
            query = " ".join(icons[:5])
            break

    if not query:
        query = " ".join(keywords[:3])

    print(f"Searching for: {query}")
    search_icons(query, limit=10)


def show_attribution(prefixes: list = None):
    """Show attribution for used icons."""
    if not prefixes:
        # Show all available attributions
        collections = load_collections()
        print("# Icon Attribution Summary")
        print()
        for prefix, info in sorted(collections.items()):
            license_info = info.get("license", {})
            print(f"## {prefix}")
            print(f"License: {license_info.get('title', 'Unknown')}")
            if license_info.get("url"):
                print(f"URL: {license_info['url']}")
            if license_info.get("requirements"):
                print(f"Requirements: {license_info['requirements']}")
            print()
    else:
        for prefix in prefixes:
            try:
                data = get_prefix_json(prefix)
                license_info = data.get("license", {})
                print(f"## {prefix}")
                print(f"License: {license_info.get('title', 'Unknown')}")
                if license_info.get("url"):
                    print(f"URL: {license_info['url']}")
                if license_info.get("requirements"):
                    print(f"Requirements: {license_info['requirements']}")
                print()
            except Exception as e:
                print(f"Failed to get info for {prefix}: {e}")


def doctor():
    """Check system health."""
    print("Iconify SVG Doctor Check")
    print("=" * 40)

    checks = []

    # Check cache dir
    cache_ok = ensure_cache_dir().exists()
    checks.append(("Cache directory", cache_ok))

    # Check bundled data
    bundled_ok = has_bundled_index()
    checks.append(("Bundled index", bundled_ok))

    # Check cache index
    cache_index_ok = get_cache_path("icons.db").exists()
    checks.append(("Cache index", cache_index_ok))

    # Check network (only if no bundled data)
    network_ok = True
    if not bundled_ok:
        try:
            collections = load_collections()
            network_ok = len(collections) > 0
        except Exception as e:
            network_ok = False
            print(f"Network error: {e}")
    checks.append(("Network connectivity", network_ok))

    # Check dependencies
    deps_ok = True
    try:
        import sqlite3
    except ImportError:
        deps_ok = False
    checks.append(("SQLite support", deps_ok))

    # Summary
    print()
    for name, ok in checks:
        status = "✓" if ok else "✗"
        print(f"{status} {name}: {'OK' if ok else 'FAILED'}")

    all_ok = all(ok for _, ok in checks)
    print()
    print(f"Overall: {'All checks passed' if all_ok else 'Some checks failed'}")
    return 0 if all_ok else 1


def main():
    parser = argparse.ArgumentParser(
        description="Iconify SVG - Search and retrieve SVG icons",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--version", action="version", version=f"iconify-skill {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-collections
    subparsers.add_parser("list-collections", help="List available icon collections")

    # search
    search_parser = subparsers.add_parser("search", help="Search for icons")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", "-l", type=int, default=20, help="Max results")
    search_parser.add_argument("--prefixes", "-p", help="Comma-separated prefixes to search")

    # get
    get_parser = subparsers.add_parser("get", help="Get SVG for an icon")
    get_parser.add_argument("icon", help="Icon in format prefix:name")
    get_parser.add_argument("--size", "-s", type=int, default=24, help="Icon size")
    get_parser.add_argument("--color", "-c", help="Icon color (hex or 'currentColor')")

    # suggest
    suggest_parser = subparsers.add_parser("suggest", help="Suggest icons for intent")
    suggest_parser.add_argument("intent", help="Natural language intent description")

    # attribution
    attr_parser = subparsers.add_parser("attribution", help="Show attribution info")
    attr_parser.add_argument("--prefixes", "-p", help="Comma-separated prefixes")

    # doctor
    subparsers.add_parser("doctor", help="Check system health")

    # build-index
    build_parser = subparsers.add_parser("build-index", help="Build search index")
    build_parser.add_argument("--force", "-f", action="store_true", help="Force rebuild")
    build_parser.add_argument("--bundle", "-b", action="store_true", help="Save to bundled data directory for offline use")
    build_parser.add_argument("--prefixes", "-p", help="Comma-separated list of icon sets to index")

    args = parser.parse_args()

    # Handle prefixes
    prefixes = None
    if hasattr(args, "prefixes") and args.prefixes:
        prefixes = [p.strip() for p in args.prefixes.split(",")]

    try:
        if args.command == "list-collections":
            list_collections()
        elif args.command == "search":
            search_icons(args.query, args.limit, prefixes)
        elif args.command == "get":
            get_svg(args.icon, args.size, args.color)
        elif args.command == "suggest":
            suggest_icons(args.intent)
        elif args.command == "attribution":
            show_attribution(prefixes)
        elif args.command == "doctor":
            sys.exit(doctor())
        elif args.command == "build-index":
            build_index(args.force, args.bundle, prefixes)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
