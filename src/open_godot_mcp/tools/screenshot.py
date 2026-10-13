"""Screenshot tools — godot_screenshot (read-only, saves to disk).

Docs: 02-Tools/Screenshot.md
  game, editor, region, burst
"""
from __future__ import annotations

from fastmcp import FastMCP

from ..context import ServerContext
from ._helpers import make_simple_tool


def register_screenshot_tools(mcp: FastMCP, ctx: ServerContext) -> None:
    make_simple_tool(
        mcp,
        ctx,
        "godot_screenshot",
        "Screenshots saved to disk (auto-allow). Actions: game(max_width?,format?,quality?),editor(viewport?,max_width?),region(rect,max_width?,source?),burst(count?,duration_ms?,interval_ms?),cleanup(max_count?,max_age_hours?). "
        "Screenshots are fallback/final-verification only — never for finding buttons (resolve via eval + .tscn paths). "
        "A-B comparisons require a LIVE render: check Engine.get_frames_drawn() advances across two evals (a pinned counter while "
        "Time.get_ticks_msec() advances usually means nothing is drawn and captures repeat byte-identical — restart with godot_game stop+play; EXCEPTION: for the editor-embedded game a pinned counter proves nothing either way (seen pinned at 2 with live captures, and stale boot-menu captures with healthy status fps) — always cross-check capture content against structured state). "
        "Call get_window().grab_focus() before a capture (move_to_foreground() is deprecated and logs an ERROR). The editor-embedded game "
        "window cannot be resized (window_set_size no-ops) — record DisplayServer.window_get_size() rather than assuming a requested size. "
        "Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first. Auto-rotation keeps last 50 (configurable via open_godot_mcp/screenshot_max_count) and deletes files older than 24h (configurable via open_godot_mcp/screenshot_max_age_hours); cleanup action forces immediate prune.",
    )
