"""Game control tools — godot_game (mixed).

Docs: 02-Tools/Game-Control.md §godot_game
  play(write): scene?, frozen?  -> {ok, runtime_ready}
  stop, pause, resume (write)
  status(read): {is_playing, runtime_connected, fps, viewport_size?}
"""
from __future__ import annotations

from fastmcp import FastMCP

from ..context import ServerContext
from ._helpers import make_simple_tool


def register_game_tools(mcp: FastMCP, ctx: ServerContext) -> None:
    make_simple_tool(
        mcp,
        ctx,
        "godot_game",
        "Game lifecycle. Actions: play(scene?,frozen?),stop,pause,resume,status,instances. Multi-instance (editor Run Multiple Instances): instances lists PIE game instances; pass params.instance=N (1-based) to status/pause/resume to target one — default is the first instance.",
    )
