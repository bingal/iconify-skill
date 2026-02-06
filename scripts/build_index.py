#!/usr/bin/env python3
"""
Build SQLite FTS5 index for fast icon searching.

Usage:
    python build_index.py [--force]
    python build_index.py --prefixes mdi,fa,bi
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import sqlite3
from datetime import datetime

# Import from iconify_cli
sys.path.insert(0, str(Path(__file__).parent))
from iconify_cli import (
    CACHE_DIR, COLLECTIONS_URL, GITHUB_COLLECTION_URL, http_get, get_cache_path, ensure_cache_dir
)

__version__ = "1.0.0"


def build_index(prefixes: list = None, force: bool = False):
    """Build SQLite FTS5 index for icons."""
    index_path = get_cache_path("icons.db")

    if index_path.exists() and not force:
        print(f"Index already exists at {index_path}")
        print("Use --force to rebuild.")
        return 0

    print("Building search index...")
    print(f"Output: {index_path}")

    # Connect to database
    conn = sqlite3.connect(str(index_path))
    cursor = conn.cursor()

    try:
        # Create tables
        print("Creating database schema...")

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

        # Load collections
        print("Fetching collections...")
        collections = http_get(COLLECTIONS_URL)

        # Filter prefixes
        if prefixes:
            collections = {k: v for k, v in collections.items() if k in prefixes}

        # Index metadata
        meta = {
            "build_time": datetime.now().isoformat(),
            "version": __version__,
            "collections_count": len(collections)
        }
        with open(get_cache_path("index_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        # Index each collection
        total_icons = 0
        errors = []

        for prefix in sorted(collections.keys()):
            try:
                print(f"  Indexing {prefix}...", end=" ")
                data = http_get(f"{GITHUB_COLLECTION_URL}/{prefix}.json")
                icons = data.get("icons", {})
                license_info = data.get("license", {})
                license_title = license_info.get("title", "Unknown")

                count = 0
                for name, icon in icons.items():
                    full_id = f"{prefix}:{name}"
                    # Get aliases from icon and parent chain
                    aliases = icon.get("aliases", {})
                    parent = icon.get("parent")
                    while parent:
                        parent_icon = icons.get(parent, {})
                        parent_aliases = parent_icon.get("aliases", {})
                        aliases.update(parent_aliases)
                        parent = parent_icon.get("parent")

                    alias_str = " ".join(aliases.keys())

                    # Insert into tables
                    cursor.execute(
                        """INSERT INTO icons (prefix, name, full_id, aliases, license)
                           VALUES (?, ?, ?, ?, ?)""",
                        (prefix, name, full_id, alias_str, license_title)
                    )
                    cursor.execute(
                        """INSERT INTO icons_fts (prefix, name, full_id, tokens)
                           VALUES (?, ?, ?, ?)""",
                        (prefix, name, full_id, f"{name} {alias_str}")
                    )
                    count += 1

                total_icons += count
                print(f"{count} icons")

            except (URLError, HTTPError, KeyError, json.JSONDecodeError) as e:
                errors.append((prefix, str(e)))
                print(f"FAILED: {e}")

        # Commit
        conn.commit()

        # Create helpful indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prefix ON icons(prefix)
        """)

        conn.commit()
        conn.close()

        # Summary
        print()
        print("=" * 50)
        print(f"Index built successfully!")
        print(f"  Collections: {len(collections)}")
        print(f"  Total icons: {total_icons}")
        print(f"  Build time: {meta['build_time']}")

        if errors:
            print()
            print(f"Errors ({len(errors)}):")
            for prefix, error in errors[:5]:
                print(f"  - {prefix}: {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")

        return 0

    except Exception as e:
        print(f"Error building index: {e}", file=sys.stderr)
        conn.close()
        return 1


def optimize_index():
    """Optimize the index for better search performance."""
    index_path = get_cache_path("icons.db")

    if not index_path.exists():
        print("No index found. Run 'build-index' first.")
        return 1

    conn = sqlite3.connect(str(index_path))
    cursor = conn.cursor()

    print("Optimizing index...")

    # Optimize FTS
    cursor.execute("INSERT INTO icons_fts(icons_fts) VALUES('optimize')")

    conn.commit()
    conn.close()

    print("Index optimized.")
    return 0


def show_stats():
    """Show index statistics."""
    index_path = get_cache_path("icons.db")

    if not index_path.exists():
        print("No index found. Run 'build-index' first.")
        return 1

    conn = sqlite3.connect(str(index_path))
    cursor = conn.cursor()

    # Get stats
    cursor.execute("SELECT COUNT(*) FROM icons")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT prefix) FROM icons")
    collections = cursor.fetchone()[0]

    # Get size
    size_kb = index_path.stat().st_size / 1024

    # Get metadata
    meta_path = get_cache_path("index_meta.json")
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        build_time = meta.get("build_time", "Unknown")
    else:
        build_time = "Unknown"

    print(f"Index Statistics")
    print("=" * 30)
    print(f"Total icons: {total:,}")
    print(f"Collections: {collections}")
    print(f"Size: {size_kb:.1f} KB")
    print(f"Built: {build_time}")

    conn.close()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Build SQLite FTS5 index for Iconify icons",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"iconify-build-index {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    build_parser = subparsers.add_parser("build", help="Build the search index")
    build_parser.add_argument("--force", "-f", action="store_true", help="Force rebuild")
    build_parser.add_argument("--prefixes", "-p", help="Comma-separated collection prefixes to index")

    # optimize
    subparsers.add_parser("optimize", help="Optimize existing index")

    # stats
    subparsers.add_parser("stats", help="Show index statistics")

    args = parser.parse_args()

    # Parse prefixes
    prefixes = None
    if hasattr(args, "prefixes") and args.prefixes:
        prefixes = [p.strip() for p in args.prefixes.split(",")]

    if args.command == "build":
        return build_index(prefixes, args.force)
    elif args.command == "optimize":
        return optimize_index()
    elif args.command == "stats":
        return show_stats()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
