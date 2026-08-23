"""Profiler tools — godot_profiler (read-only).

Docs: 02-Tools/Diagnostics.md §godot_profiler
  snapshot, series, spikes
"""
from __future__ import annotations

from fastmcp import FastMCP

from ..context import ServerContext
from ._helpers import make_simple_tool


def register_profiler_tools(mcp: FastMCP, ctx: ServerContext) -> None:
    make_simple_tool(
        mcp,
        ctx,
        "godot_profiler",
        "Performance profiling (auto-allow, game must run). Actions: snapshot,series(duration_ms?,metrics?),spikes(threshold_ms?). Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first.",
    )
