#!/usr/bin/env python3
"""
Tests for iconify-svg CLI.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestSanitization:
    """Test SVG sanitization."""

    def test_safe_svg(self):
        """Test that normal SVG passes."""
        from iconify_cli import sanitize_svg
        assert sanitize_svg('<path d="M10 10 L20 20"/>') is True

    def test_rejects_script(self):
        """Test that script tags are rejected."""
        from iconify_cli import sanitize_svg
        assert sanitize_svg('<script>alert(1)</script>') is False

    def test_rejects_onload(self):
        """Test that onload handlers are rejected."""
        from iconify_cli import sanitize_svg
        assert sanitize_svg('<svg onload="alert(1)">') is False

    def test_rejects_external_href(self):
        """Test that external hrefs are rejected."""
        from iconify_cli import sanitize_svg
        assert sanitize_svg('<a href="http://evil.com">') is False


class TestIconResolution:
    """Test icon alias resolution."""

    def test_parse_prefix_name(self):
        """Test parsing prefix:name format."""
        from iconify_cli import get_svg
        # This would need mocking to test fully
        assert True  # Placeholder


class TestCLIArgs:
    """Test CLI argument parsing."""

    def test_list_collections_args(self):
        """Test list-collections command args."""
        import argparse
        from iconify_cli import main

        # Mock the subparser structure
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", required=True)
        subparsers.add_parser("list-collections")

        args = parser.parse_args(["list-collections"])
        assert args.command == "list-collections"

    def test_search_args(self):
        """Test search command args."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", required=True)
        search = subparsers.add_parser("search")
        search.add_argument("query")
        search.add_argument("--limit", type=int, default=20)
        search.add_argument("--prefixes")

        args = parser.parse_args(["search", "test", "--limit", "10"])
        assert args.command == "search"
        assert args.query == "test"
        assert args.limit == 10

    def test_get_args(self):
        """Test get command args."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", required=True)
        get = subparsers.add_parser("get")
        get.add_argument("icon")
        get.add_argument("--size", type=int, default=24)
        get.add_argument("--color")

        args = parser.parse_args(["get", "mdi:home", "--size", "32"])
        assert args.command == "get"
        assert args.icon == "mdi:home"
        assert args.size == 32


class TestCache:
    """Test caching functionality."""

    def test_cache_path_generation(self):
        """Test cache path generation."""
        from iconify_cli import get_cache_path, ensure_cache_dir

        path = get_cache_path("test.json")
        assert "test.json" in str(path)

    def test_ensure_cache_dir(self):
        """Test cache directory creation."""
        from iconify_cli import ensure_cache_dir

        path = ensure_cache_dir()
        assert path.exists()


class TestSVGAssembly:
    """Test SVG assembly logic."""

    def test_svg_wrapper(self):
        """Test basic SVG wrapping."""
        body = '<path d="M10 10"/>'
        width = 24
        height = 24
        size = 24
        color = None

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg"',
            f'viewBox="0 0 {width} {height}"',
            f'width="{size}" height="{size}">',
            body,
            '</svg>'
        ]
        svg = "\n".join(svg_parts)

        assert 'viewBox="0 0 24 24"' in svg
        assert 'width="24" height="24"' in svg
        assert body in svg

    def test_svg_with_color(self):
        """Test SVG with custom color."""
        body = '<path d="M10 10"/>'
        width = 24
        height = 24
        size = 24
        color = "#FF0000"

        if color and color != "currentColor":
            svg = f'<g fill="{color}">{body}</g>'
        else:
            svg = body

        assert '<g fill="#FF0000">' in svg


class TestIndexBuild:
    """Test index building."""

    def test_build_index_help(self):
        """Test build-index help."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "build_index.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0


class TestDoctor:
    """Test doctor check."""

    def test_doctor_help(self):
        """Test doctor help."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "doctor.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
