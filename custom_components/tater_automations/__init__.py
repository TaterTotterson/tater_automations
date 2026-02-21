from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, CONF_HOST, CONF_PORT, DEFAULT_PORT, SERVICE_CALL_TOOL

PLATFORMS: list[str] = []
STRING_ARGUMENT_FIELDS: tuple[str, ...] = (
    "area",
    "camera",
    "timeframe",
    "query",
    "input_text_entity",
    "tone",
    "prompt_hint",
)
INTEGER_ARGUMENT_FIELDS: tuple[str, ...] = ("hours",)
BOOLEAN_ARGUMENT_FIELDS: tuple[str, ...] = ("include_date",)

TOOL_ALLOWED_ARGUMENTS: dict[str, set[str]] = {
    "camera_event": {"area", "camera"},
    "doorbell_alert": set(),
    "events_query_brief": {"area", "timeframe", "query", "input_text_entity"},
    "weather_brief": {"hours", "query", "input_text_entity"},
    "zen_greeting": {"include_date", "tone", "prompt_hint", "input_text_entity"},
}

async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    session = aiohttp_client.async_get_clientsession(hass)

    def _coerce_bool(field: str, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "y", "on", "enabled"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", "disabled"}:
            return False
        raise HomeAssistantError(f"{field} must be true/false")

    def _coerce_value(field: str, value: Any) -> Any:
        if field in STRING_ARGUMENT_FIELDS:
            return str(value).strip()
        if field in INTEGER_ARGUMENT_FIELDS:
            try:
                return int(value)
            except (TypeError, ValueError) as e:
                raise HomeAssistantError(f"{field} must be a whole number") from e
        if field in BOOLEAN_ARGUMENT_FIELDS:
            return _coerce_bool(field, value)
        return value

    def _build_arguments(call: ServiceCall, tool: str) -> dict[str, Any]:
        arguments = call.data.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise HomeAssistantError("arguments must be an object/dict")

        allowed_fields = TOOL_ALLOWED_ARGUMENTS.get(tool, set())
        merged_arguments: dict[str, Any] = {}

        for field in allowed_fields:
            value = arguments.get(field)
            if value in (None, ""):
                continue
            merged_arguments[field] = _coerce_value(field, value)

        for field in allowed_fields:
            value = call.data.get(field)
            if value in (None, ""):
                continue
            merged_arguments[field] = _coerce_value(field, value)

        return merged_arguments

    async def _call_tool(call: ServiceCall):
        tool = (call.data.get("tool") or "").strip()
        if not tool:
            raise HomeAssistantError("Missing required field: tool")
        arguments = _build_arguments(call, tool)

        url = f"http://{host}:{port}/tater-ha/v1/tools/{tool}"
        payload = {"arguments": arguments}

        try:
            async with session.post(url, json=payload, timeout=15) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise HomeAssistantError(f"Tater tool call failed ({resp.status}): {text[:200]}")
                # Return value is not used by automations directly, but shows in traces/logs
                try:
                    return json.loads(text) if text else {"ok": True}
                except Exception:
                    return {"ok": True, "raw": text}
        except asyncio.TimeoutError as e:
            raise HomeAssistantError("Tater tool call timed out") from e
        except Exception as e:
            raise HomeAssistantError(f"Tater tool call error: {e}") from e

    hass.services.async_register(DOMAIN, SERVICE_CALL_TOOL, _call_tool)
    return True

async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    hass.services.async_remove(DOMAIN, SERVICE_CALL_TOOL)
    return True
