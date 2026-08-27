"""Small, deterministic indexes for Agent-facing 10-K research workflows."""

from .materialize import IndexBuildResult, materialize_index
from .search import search_index, read_markdown_lines

__all__ = [
    "IndexBuildResult",
    "materialize_index",
    "search_index",
    "read_markdown_lines",
]
