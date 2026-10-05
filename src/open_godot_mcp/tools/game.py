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
        "Game lifecycle. Actions: play(scene?,frozen?),stop,pause,resume,status,instances. Always pass play scene explicitly "
        "(res:// path or \"main\"); never rely on whatever scene is open in the editor. Param-name trap: godot_editor_edit open_scene "
        "takes params.path, only godot_game play takes scene. Wait for runtime_ready=true (else poll status) and verify the expected "
        "in-world state (e.g. menu hidden + player node exists) before driving input. "
        "Multi-instance (editor Run Multiple Instances): instances lists PIE game instances (pid, launch args, ready); pass params.instance=N "
        "(1-based) to status/pause/resume to target one — default is the first instance. Pids change across stop/play; re-establish assumed state. "
        "Drive instances sequentially, not batched. Prove routing with a pid stamp (OS.get_process_id()) vs instances when two views look identical.",
    )
