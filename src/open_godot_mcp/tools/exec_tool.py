"""Exec tools — godot_exec (write, gated, GDScript injection).

Docs: 02-Tools/Runtime-State.md §godot_exec
  eval, call
"""
from __future__ import annotations

from fastmcp import FastMCP

from ..context import ServerContext
from ..utils.error_codes import fail
from ._helpers import make_tool, route_tool


def register_exec_tools(mcp: FastMCP, ctx: ServerContext) -> None:
    @make_tool(
        mcp,
        ctx,
        "godot_exec",
        "Execute GDScript in running game (gated). Actions: eval(code,await?),call(node_path,method,args?),assert(condition,description?,await?). Disabled if --no-eval. "
        "Coordinate evals must return a flat {\"x\",\"y\"} dict (e.g. var p=center; return {\"x\":int(p.x),\"y\":int(p.y)}) — "
        "raw Vector2 does not survive bridge encoding. No for/while loops in eval (they time out); use map/filter or single-node access, "
        "scope find_children to the smallest subtree and slice results. An eval TIMEOUT usually means the body errored — "
        "check godot_log errors before retrying. Avoid touching MeshInstance3D.mesh resources in eval; prefer transforms, "
        "is_position_in_frustum, physics raycasts. C# export props are reachable via get()/set() (e.g. rig.get(\"PitchDegrees\")), not direct member syntax. "
        "An eval that errors or times out can trip the editor break-on-error and pin the frame loop while evals still answer: "
        "check godot_debugger sessions (paused:true), then recover with godot_game stop + play — resume re-breaks. Never await inside "
        "an eval body (\"Trying to call an async function without \"await\" wedges the loop). Never return multi-MB strings (full state dumps) "
        "through the bridge — an oversized reply can trip the editor websocket (ERR_OUT_OF_MEMORY); stash it with node.set_meta('dump', s) and "
        "read slices with String.find/substr in later evals. Never issue an eval in the same execute/round-trip as godot_game play (races the attach: RUNTIME_NOT_CONNECTED) — read godot_game status first; right after a sector/level launch, deferred work can time out even a single-statement eval — wait/poll a trivial eval first. get_meta() on a missing key logs an error — guard with has_meta(). Known-timeout eval bodies (all pin the loop the same way): campaign_views_json (even a plain call), MindRender.get_stats() while a sector is loaded, tile_blocks() walked with a loop, JSON.parse_string(get_state_json()) + filter over the sparse tiles, filter/map lambdas over mixed rows, for-loops over dialog children — query one known node per eval instead. Prefer single-statement evals: a statement-level if/for that mutates can pin too. Keep every var declaration at the eval top level (a var nested in an if block errors). A method the node does not expose (wrong facade, renamed/removed fn) errors and pins like any bad body, and a Rust pub fn without #[func] is not eval-reachable (Invalid call: Nonexistent function) — use a #[func] sibling or the real input path. Read hover from get_tree().root.gui_get_hovered_control() (an eval node has no get_viewport() context). Budget is 15 s and a timed-out call keeps running and blocks later evals — chunk big steps (e.g. 6-10 x step(600)) and poll. A wrong-arity Rust call (e.g. campaign_views_json with 0 args, start_sector with 3) burns the full timeout via the godot-rust error without pinning — check the log before assuming a freeze. "
        "Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first.",
        is_write=True,
    )
    async def godot_exec(action: str, params: dict | None = None) -> dict:
        # Extra security gate for eval
        if action == "eval" and not ctx.allow_eval:
            return fail("PERMISSION_DENIED", "godot_exec eval is disabled (--no-eval)")
        return await route_tool(ctx, "godot_exec", action, params, is_write=True)
