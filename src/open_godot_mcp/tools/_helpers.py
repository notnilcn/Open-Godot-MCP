"""Shared helpers for tool modules.

Every tool is a FastMCP function taking ``action: str`` and ``params: dict``.
FastMCP does not support **kwargs, so action-specific parameters go inside
the ``params`` dict. We route to the bridge via ``ctx.call(tool, action, params)``.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable

from fastmcp import FastMCP

from ..context import ServerContext
from ..utils.error_codes import fail

# The published signature for every tool. Kept explicit because functools.wraps
# would otherwise copy an untyped lambda's signature over the wrapper's own.
_TOOL_ANNOTATIONS = {"action": str, "params": dict | None, "return": dict}


def coerce_params(params: object) -> dict:
    """Normalize the ``params`` argument into a plain dict.

    Clients may send the object itself or a JSON-encoded string, so accept both.
    """
    if params is None or params == "":
        return {}
    if isinstance(params, str):
        try:
            decoded = json.loads(params)
        except json.JSONDecodeError as e:
            raise ValueError(f"params must be an object or a JSON object string: {e}") from e
        if not isinstance(decoded, dict):
            raise ValueError(f"params must be an object, got {type(decoded).__name__}")
        return decoded
    if isinstance(params, dict):
        return dict(params)
    raise ValueError(f"params must be an object, got {type(params).__name__}")


def pop_instance_id(params: dict) -> tuple[dict, str | None]:
    """Strip the optional ``instance_id`` key from params (Index.md §跨領域可選參數)."""
    if not isinstance(params, dict):
        return params, None
    iid = params.pop("instance_id", None)
    return params, iid


def guard_write(ctx: ServerContext) -> dict | None:
    """Return a fail dict if writes are blocked, else None."""
    if ctx.read_only:
        return fail("PERMISSION_DENIED", "Server is in read-only mode")
    return None


async def route_tool(
    ctx: ServerContext,
    tool: str,
    action: str,
    params: dict | None,
    *,
    is_write: bool = False,
) -> dict:
    """Standard tool body: guard write -> strip instance_id -> call bridge."""
    if is_write:
        blocked = guard_write(ctx)
        if blocked:
            return blocked
    params = coerce_params(params)
    params, iid = pop_instance_id(params)
    return await ctx.call(tool, action, params, instance_id=iid)


def make_tool(
    mcp: FastMCP,
    ctx: ServerContext,
    name: str,
    description: str,
    *,
    is_write: bool = False,
) -> Callable:
    """Decorator: register an async tool ``(action, params) -> dict`` on *mcp*.

    Handles read-only guard, exception -> fail dict conversion.
    The wrapped fn receives (action, params) and should call route_tool() itself
    so it can add per-tool validation before routing.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(action: str, params: dict | None = None) -> dict:
            if is_write:
                blocked = guard_write(ctx)
                if blocked:
                    return blocked
            try:
                result: dict = await fn(action, coerce_params(params))
                return result
            except TypeError as e:
                return fail("INVALID_ARGUMENT", str(e))
            except ValueError as e:
                return fail("INVALID_ARGUMENT", str(e))
            except Exception as e:  # noqa: BLE001
                return fail("INTERNAL_ERROR", f"{type(e).__name__}: {e}")

        # functools.wraps copies __wrapped__ and __annotations__ off *fn*, which for
        # make_simple_tool is an untyped lambda. inspect.signature() follows those, so
        # FastMCP would publish action/params with no type at all -- and clients faced
        # with an untyped param send it as a JSON string. Pin the real signature back.
        wrapper.__annotations__ = dict(_TOOL_ANNOTATIONS)
        del wrapper.__wrapped__

        mcp.tool(name=name, description=description)(wrapper)
        return wrapper

    return decorator


def make_simple_tool(
    mcp: FastMCP,
    ctx: ServerContext,
    name: str,
    description: str,
    *,
    is_write: bool = False,
) -> None:
    """Register a tool that just routes to the bridge with no local validation."""
    make_tool(mcp, ctx, name, description, is_write=is_write)(
        lambda action, params=None: route_tool(ctx, name, action, params, is_write=is_write)
    )
