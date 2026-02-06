#!/usr/bin/env python3
"""
Update script for iconify-skill bundled data.

Downloads icon metadata and builds the search index for offline use.

Usage:
    python update_bundled_data.py [--collections mdi,bi,lucide]

This script:
1. Fetches icon collection metadata from GitHub
2. Builds SQLite FTS5 index for searching
3. Saves bundled data to data/ directory
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Constants
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR / "data"
BUNDLE_ZIP = DATA_DIR / "icons.zip"
INDEX_DB = DATA_DIR / "icons.db"
METADATA_FILE = DATA_DIR / "collections.json"
GITHUB_RAW = "https://raw.githubusercontent.com/iconify/icon-sets/master/json"
ICONIFY_API = "https://api.iconify.design"
COLLECTIONS_URL = f"{ICONIFY_API}/collections"

__version__ = "1.0.0"


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def http_get(url: str, timeout: float = 30.0) -> dict:
    """Fetch JSON from URL."""
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": f"iconify-skill-update/{__version__}"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")


def load_collections():
    """Load available collections list."""
    print("Fetching collections list...")
    return http_get(COLLECTIONS_URL)


def build_index(collections: dict, prefixes: list = None):
    """Build SQLite FTS5 index for icons."""
    print("Building search index...")
    
    conn = sqlite3.connect(str(INDEX_DB))
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

    total_icons = 0
    for prefix in sorted(collections.keys()):
        if prefixes and prefix not in prefixes:
            continue
            
        try:
            print(f"  Indexing {prefix}...", end=" ", flush=True)
            data = http_get(f"{GITHUB_RAW}/{prefix}.json")
            icons = data.get("icons", {})
            license_info = data.get("license", {})
            license_title = license_info.get("title", "Unknown")

            count = 0
            for name, icon in icons.items():
                full_id = f"{prefix}:{name}"
                aliases = icon.get("aliases", {})
                parent = icon.get("parent")
                while parent:
                    parent_icon = icons.get(parent, {})
                    parent_aliases = parent_icon.get("aliases", {})
                    aliases.update(parent_aliases)
                    parent = parent_icon.get("parent")

                alias_str = " ".join(aliases.keys())

                cursor.execute(
                    "INSERT INTO icons (prefix, name, full_id, aliases, license) VALUES (?, ?, ?, ?, ?)",
                    (prefix, name, full_id, alias_str, license_title)
                )
                cursor.execute(
                    "INSERT INTO icons_fts (prefix, name, full_id, tokens) VALUES (?, ?, ?, ?)",
                    (prefix, name, full_id, f"{name} {alias_str}")
                )
                count += 1
                total_icons += 1

            print(f"{count} icons")

        except Exception as e:
            print(f"Failed: {e}")
            continue

    conn.commit()
    conn.close()
    
    return total_icons


def save_metadata(collections: dict, prefixes: list = None):
    """Save collection metadata to bundled file."""
    if prefixes:
        filtered = {k: v for k, v in collections.items() if k in prefixes}
    else:
        filtered = collections
    
    with open(METADATA_FILE, "w") as f:
        json.dump(filtered, f, indent=2)
    
    print(f"Saved metadata for {len(filtered)} collections to {METADATA_FILE}")


def create_bundle():
    """Create zip archive of bundled data."""
    print(f"Creating bundle archive...")
    
    with zipfile.ZipFile(BUNDLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(INDEX_DB, "icons.db")
        zf.write(METADATA_FILE, "collections.json")
        
        # Add version info
        version_info = {
            "version": __version__,
            "created_at": datetime.now().isoformat(),
            "bundled_collections": get_bundled_count()
        }
        zf.writestr("version.json", json.dumps(version_info, indent=2))
    
    print(f"Bundle created: {BUNDLE_ZIP} ({BUNDLE_ZIP.stat().st_size / 1024:.1f} KB)")


def get_bundled_count() -> int:
    """Get number of icons in bundled index."""
    if not INDEX_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(INDEX_DB))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM icons")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def verify_bundle():
    """Verify bundled data is valid."""
    print("Verifying bundle...")
    
    issues = []
    
    if not INDEX_DB.exists():
        issues.append("icons.db not found")
    else:
        try:
            conn = sqlite3.connect(str(INDEX_DB))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM icons")
            count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM icons_fts")
            fts_count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                issues.append("icons table is empty")
            if fts_count == 0:
                issues.append("icons_fts table is empty")
            if count != fts_count:
                issues.append(f"Icon count mismatch: icons={count}, fts={fts_count}")
                
        except Exception as e:
            issues.append(f"Database error: {e}")
    
    if not METADATA_FILE.exists():
        issues.append("collections.json not found")
    
    if issues:
        print("❌ Bundle verification failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        count = get_bundled_count()
        print(f"✅ Bundle verified: {count} icons indexed")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Update iconify-skill bundled data for offline use",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--collections", "-c", help="Comma-separated list of collections to index")
    parser.add_argument("--verify", action="store_true", help="Verify existing bundle")
    parser.add_argument("--version", action="version", version=f"iconify-skill-update {__version__}")

    args = parser.parse_args()

    print("=" * 50)
    print(f"iconify-skill-update v{__version__}")
    print("=" * 50)

    if args.verify:
        verify_bundle()
        return 0

    # Parse prefixes
    prefixes = None
    if args.collections:
        prefixes = [p.strip() for p in args.collections.split(",")]
        print(f"Filtering to: {', '.join(prefixes)}")

    # Ensure data directory
    ensure_data_dir()

    # Load collections
    collections = load_collections()

    # Save metadata
    save_metadata(collections, prefixes)

    # Build index
    total_icons = build_index(collections, prefixes)

    # Create bundle
    create_bundle()

    # Verify
    if verify_bundle():
        print("\n" + "=" * 50)
        print(f"✅ Update complete! Bundled {total_icons} icons")
        print("=" * 50)
        return 0
    else:
        print("\n" + "=" * 50)
        print("❌ Update failed: bundle verification failed")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
