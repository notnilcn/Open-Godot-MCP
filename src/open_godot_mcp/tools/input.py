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
        "(default frame_delay:1 is what makes it land); do not split press/release. sequence takes "
        "{\"steps\":[{\"type\":...,\"params\":{...}}],\"frame_delay\":1}; the flat {\"events\":[...]} form is rejected and injects nothing. "
        "If sequence times out while plain eval still answers, the frame loop is stalled — recover with godot_game stop+play. "
        "After a discrete press/release, flush with Input.flush_buffered_events() in an eval and assert the target state in that same eval — "
        "unflushed input sits in the accumulated buffer and looks like a dead UI. World presses inside a visible STOP-filter Control "
        "(banner/overlay) are dropped: probe gui_get_hovered_control() at the point before suspecting the input path. "
        "DRAG = motion to A, press at A, "
        "motion to B with button_mask:[\"MOUSE_BUTTON_LEFT\"], release at B; verify gui_is_dragging(). "
        "HOVER = mouse_motion then next call verify get_tree().root.gui_get_hovered_control() "
        "(input dispatches next frame; get_viewport().get_mouse_position() reads the OS cursor — ignore it). "
        "key names are plain (Tab,E,Up) not KEY_TAB (silently no-ops). godot_input text is broken: the runtime reuses one InputEventKey for press+release in the same frame, the engine discards it and the field stays empty (plus a log error); godot_input key sets no unicode so LineEdit ignores it. Type by pushing a FRESH InputEventKey down+up per char in eval, or set field.text + emit text_changed and click OK with real mouse input. No wheel action exists: scroll/rotate by pushing InputEventMouseButton WHEEL_UP/DOWN (pressed=true, factor=1.0, position set) through the viewport in eval. sequence frame_delay counts PROCESS frames (wall time), not sim ticks — for exact ticks drive paused + step. Known STOP traps: HUD hints full-screen panel, LoadingLayer loading overlay (check io_pending/step to drain); an OverlayLayer fragment Button can hover yet never activate — fallback is emitting pressed (staging only). Fade-dependent menu walks go one click per call — a click can return ok and still miss while a submenu fades; probe the expected dialog/submenu node between clicks, and never resolve a click from a sentinel read (e.g. sel -1 right after OK) — re-probe once. Drive same-frame container rebuilds (close+open palette) as two calls and resolve targets by content (tooltip_text), skipping is_queued_for_deletion() nodes — child names get auto-renamed. "
        "Multi-instance: params.instance=N (1-based, godot_game instances lists them) targets one PIE game instance; default is the first.",
        is_write=True,
    )
