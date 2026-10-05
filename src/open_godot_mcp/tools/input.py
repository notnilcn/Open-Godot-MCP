"""Input tools — godot_input (write, gated).

Docs: 02-Tools/Input.md
  action, key, mouse_button, mouse_motion, joypad, text
"""
from __future__ import annotations

from fastmcp import FastMCP

from ..context import ServerContext
from ._helpers import make_simple_tool


def register_input_tools(mcp: FastMCP, ctx: ServerContext) -> None:
    make_simple_tool(
        mcp,
        ctx,
        "godot_input",
        "Inject input into running game (gated). Actions: action,key,mouse_button,mouse_motion,joypad,text,record_start,record_stop,replay,sequence. "
        "UI driving: resolve the target Control center via godot_exec eval "
        "`(get_node(\"<path>\") as Control).get_global_rect().get_center()` and pass coords:\"viewport\" — "
        "never hardcode coords, never screenshot-hunt buttons. CLICK = ONE sequence call with press+release "
        "(default frame_delay:1 is what makes it land); do not split press/release. DRAG = motion to A, press at A, "
        "motion to B with button_mask:[\"MOUSE_BUTTON_LEFT\"], release at B; verify gui_is_dragging(). "
        "HOVER = mouse_motion then next call verify get_tree().root.gui_get_hovered_control() "
        "(input dispatches next frame; get_viewport().get_mouse_position() reads the OS cursor — ignore it). "
        "key names are plain (Tab,E,Up) not KEY_TAB (silently no-ops). "
        "Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first.",
        is_write=True,
    )
