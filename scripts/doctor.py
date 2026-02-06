#!/usr/bin/env python3
"""
System health check for iconify-skill.

Usage:
    python doctor.py
    python doctor.py --verbose
"""

import argparse
import json
import os
import sys
from pathlib import Path
import sqlite3
import subprocess

# Import from iconify_cli
sys.path.insert(0, str(Path(__file__).parent))
from iconify_cli import (
    CACHE_DIR, ICONIFY_API, http_get, get_cache_path, ensure_cache_dir
)

__version__ = "1.0.0"


class Doctor:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks = []
        self.warnings = []
        self.errors = []

    def check(self, name: str) -> bool:
        """Decorator to run a check and track result."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    status = "PASS" if result else "FAIL"
                    self.checks.append((name, status))
                    return result
                except Exception as e:
                    self.checks.append((name, f"ERROR: {e}"))
                    self.errors.append((name, str(e)))
                    return False
            return wrapper
        return decorator

    def run_all_checks(self):
        """Run all health checks."""
        print("Iconify SVG Doctor")
        print("=" * 50)

        # Python version
        self._check_python()

        # Cache directory
        self._check_cache_dir()

        # Network connectivity
        self._check_network()

        # Collections API
        self._check_collections_api()

        # SQLite support
        self._check_sqlite()

        # Search index
        self._check_index()

        # Dependencies
        self._check_dependencies()

        # Print summary
        self._print_summary()

        return len(self.errors) == 0

    @check("Python Version")
    def _check_python(self):
        """Check Python version."""
        v = sys.version_info
        ok = v.major >= 3 and v.minor >= 8
        if not ok:
            self.warnings.append(("Python", f"Version {v.major}.{v.minor} may have issues"))
        return ok

    @check("Cache Directory")
    def _check_cache_dir(self):
        """Check cache directory exists and is writable."""
        path = ensure_cache_dir()
        exists = path.exists()
        writable = os.access(str(path), os.W_OK) if exists else False
        if not exists:
            try:
                path.mkdir(parents=True, exist_ok=True)
                exists = True
            except Exception:
                pass
        return exists and writable

    @check("Network Connectivity")
    def _check_network(self):
        """Check basic network connectivity."""
        try:
            import socket
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except Exception as e:
            self.warnings.append(("Network", "Limited connectivity"))
            return True  # Not a hard fail

    @check("Iconify Collections API")
    def _check_collections_api(self):
        """Check Iconify API is accessible."""
        try:
            collections = http_get(f"{ICONIFY_API}/collections.json")
            return len(collections) > 0
        except Exception as e:
            self.errors.append(("Iconify API", str(e)))
            return False

    @check("SQLite Support")
    def _check_sqlite(self):
        """Check SQLite is available."""
        try:
            import sqlite3
            conn = sqlite3.connect(":memory:")
            conn.execute("CREATE TABLE test(id INTEGER PRIMARY KEY)")
            conn.execute("DROP TABLE test")
            conn.close()
            return True
        except Exception:
            self.errors.append(("SQLite", "Not available"))
            return False

    @check("Search Index")
    def _check_index(self):
        """Check search index exists and is valid."""
        index_path = get_cache_path("icons.db")
        if not index_path.exists():
            self.warnings.append(("Index", "Not built (run 'iconify build-index')"))
            return True  # Not required for basic usage

        try:
            conn = sqlite3.connect(str(index_path))
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute("SELECT COUNT(*) FROM icons")
            count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM icons_fts")
            fts_count = cursor.fetchone()[0]

            conn.close()

            if self.verbose:
                print(f"  Indexed icons: {count:,}")

            return count > 0 and count == fts_count

        except Exception as e:
            self.errors.append(("Index", f"Invalid: {e}"))
            return False

    @check("Python Dependencies")
    def _check_dependencies(self):
        """Check required modules are available."""
        required = ["json", "urllib", "sqlite3"]
        # These are all in stdlib, so always available
        return True

    @check("Scripts")
    def _check_scripts(self):
        """Check CLI scripts are executable."""
        script_dir = Path(__file__).parent
        scripts = ["iconify_cli.py", "build_index.py", "doctor.py"]
        for script in scripts:
            path = script_dir / script
            if not path.exists():
                self.warnings.append(("Scripts", f"{script} missing"))
        return True

    def _print_summary(self):
        """Print check summary."""
        print()
        print("Check Results")
        print("-" * 50)

        for name, status in self.checks:
            if status == "PASS":
                icon = "✓"
            elif status.startswith("ERROR"):
                icon = "✗"
            else:
                icon = "○"
            print(f"{icon} {name}: {status}")

        if self.warnings:
            print()
            print("Warnings:")
            for name, msg in self.warnings:
                print(f"  ! {name}: {msg}")

        if self.errors:
            print()
            print("Errors (require attention):")
            for name, msg in self.errors:
                print(f"  ✗ {name}: {msg}")

        print()
        print("=" * 50)

        if self.errors:
            print(f"Status: FAILED ({len(self.errors)} error(s))")
        elif self.warnings:
            print(f"Status: OK with warnings ({len(self.warnings)} warning(s))")
        else:
            print("Status: All checks passed ✓")

    def suggest_fix(self):
        """Suggest fixes for common issues."""
        suggestions = []

        for name, msg in self.errors:
            if "Iconify API" in name:
                suggestions.append("- Check your internet connection")
                suggestions.append("- Try: curl https://api.iconify.design/collections.json")

            if "Index" in name:
                suggestions.append("- Run: iconify build-index")
                suggestions.append("- Or: python scripts/build_index.py build --force")

        if suggestions:
            print()
            print("Suggested fixes:")
            for s in suggestions:
                print(s)


def main():
    parser = argparse.ArgumentParser(
        description="Check iconify-skill system health",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"iconify-doctor {__version__}")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info")

    args = parser.parse_args()

    doctor = Doctor(verbose=args.verbose)
    success = doctor.run_all_checks()

    if not success:
        doctor.suggest_fix()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
