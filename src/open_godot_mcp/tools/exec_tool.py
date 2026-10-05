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
        "Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first.",
        is_write=True,
    )
    async def godot_exec(action: str, params: dict | None = None) -> dict:
        # Extra security gate for eval
        if action == "eval" and not ctx.allow_eval:
            return fail("PERMISSION_DENIED", "godot_exec eval is disabled (--no-eval)")
        return await route_tool(ctx, "godot_exec", action, params, is_write=True)
