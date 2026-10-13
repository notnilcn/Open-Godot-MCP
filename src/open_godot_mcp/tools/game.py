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
        "in-world state (e.g. menu hidden + player node exists) before driving input. Never issue the first eval in the same execute block as play — it races the attach (RUNTIME_NOT_CONNECTED); read status first. After a sector/level launch the runtime still has deferred UI work — wait/poll before evals. "
        "status fps/process_time come from the editor and can read healthy while the game frame loop is frozen — prove liveness with an "
        "eval (Time.get_ticks_msec() delta across two calls). An editor-embedded game window cannot be resized (window_set_size no-ops); "
        "read DisplayServer.window_get_size() instead of assuming a requested size took effect. "
        "Multi-instance (editor Run Multiple Instances): instances lists PIE game instances (pid, launch args, ready); pass params.instance=N "
        "(1-based) to status/pause/resume to target one — default is the first instance. Pids change across stop/play; re-establish assumed state. A fresh game is UNPAUSED after stop/play: the fixed-step pump advances during each round-trip — pause before taking step/load measurements. After play, inject input only once the loop actually runs (poll Engine.get_process_frames() > 0; the first clicks can land while frames are still 0). "
        "Drive instances sequentially, not batched. Prove routing with a pid stamp (OS.get_process_id()) vs instances when two views look identical. play reports runtime_ready=true before the runtime attaches — poll status until runtime_connected (takes ~5 s); only a persistently false status is broken. stop kills the process with no scene teardown (exit_tree/dispose hooks never fire) — exercise dispose paths with eval get_tree().quit() then check files. stop leaves launchid.dat so the next boot warns 'may have crashed' — benign; compare crash-dir mtimes. Orphan game processes survive stop+editor kills and burn CPU — sweep pgrep after sessions. Always relaunch the editor after rebuilding the GDExtension (mmap'd at editor start); prove freshness with a has_method probe, not the .so mtime."
    )
