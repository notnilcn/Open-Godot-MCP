"""Game time tools — godot_game_time (write, deterministic clock control).

Docs: 02-Tools/Game-Control.md §godot_game_time
  freeze, unfreeze, step, step_until
"""
from __future__ import annotations

from fastmcp import FastMCP

from ..context import ServerContext
from ._helpers import make_simple_tool


def register_game_time_tools(mcp: FastMCP, ctx: ServerContext) -> None:
    make_simple_tool(
        mcp,
        ctx,
        "godot_game_time",
        "Deterministic clock control (gated). Actions: freeze,unfreeze,step(ms,inputs?),step_until(condition,timeout_ms?,interval_ms?). "
        "sequence/input-step timeouts while plain eval still answers mean the frame loop stalled (input awaits process_frame; eval uses the debugger channel) — "
        "diagnose by reading Engine.get_process_frames() twice; no advance = stalled, fix with godot_game stop+play. "
        "Drive closed-loop (re-read state after each drive), never by wall-clock dead-reckoning. "
        "Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first.",
        is_write=True,
    )
