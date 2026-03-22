from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client

from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_API_KEY,
    DEFAULT_PORT,
    DOMAIN,
    SERVICE_CALL_CAMERA_EVENT,
    SERVICE_CALL_DOORBELL_ALERT,
    SERVICE_CALL_EVENTS_QUERY_BRIEF,
    SERVICE_CALL_TOOL,
    SERVICE_CALL_WEATHER_BRIEF,
    SERVICE_CALL_ZEN_GREETING,
)

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
SERVICE_FIXED_TOOL: dict[str, str] = {
    SERVICE_CALL_CAMERA_EVENT: "camera_event",
    SERVICE_CALL_DOORBELL_ALERT: "doorbell_alert",
    SERVICE_CALL_EVENTS_QUERY_BRIEF: "events_query_brief",
    SERVICE_CALL_WEATHER_BRIEF: "weather_brief",
    SERVICE_CALL_ZEN_GREETING: "zen_greeting",
}
REGISTERED_SERVICES: tuple[str, ...] = (SERVICE_CALL_TOOL, *tuple(SERVICE_FIXED_TOOL.keys()))

async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    cfg = dict(entry.data)
    cfg.update(entry.options or {})
    host = cfg.get(CONF_HOST)
    port = cfg.get(CONF_PORT, DEFAULT_PORT)
    api_key = str(cfg.get(CONF_API_KEY) or "").strip()

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

    def _build_arguments(call: ServiceCall, tool: str, *, include_raw_arguments: bool) -> dict[str, Any]:
        raw_arguments = call.data.get("arguments") if include_raw_arguments else {}
        if raw_arguments is None:
            raw_arguments = {}
        if not isinstance(raw_arguments, dict):
            raise HomeAssistantError("arguments must be an object/dict")

        allowed_fields = TOOL_ALLOWED_ARGUMENTS.get(tool, set())
        merged_arguments: dict[str, Any] = {}

        for field in allowed_fields:
            value = raw_arguments.get(field)
            if value in (None, ""):
                continue
            merged_arguments[field] = _coerce_value(field, value)

        for field in allowed_fields:
            value = call.data.get(field)
            if value in (None, ""):
                continue
            merged_arguments[field] = _coerce_value(field, value)

        return merged_arguments

    async def _post_tool(tool: str, arguments: dict[str, Any]):
        url = f"http://{host}:{port}/tater-ha/v1/tools/{tool}"
        payload = {"arguments": arguments}
        request_kwargs: dict[str, Any] = {"json": payload, "timeout": 15}
        if api_key:
            request_kwargs["headers"] = {"X-Tater-Token": api_key}

        try:
            async with session.post(url, **request_kwargs) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    detail = text[:200]
                    if resp.status in (401, 403):
                        if api_key:
                            auth_hint = "Invalid API key. Update Tater Automations integration settings."
                        else:
                            auth_hint = "API key required. Set it in Tater Automations integration settings."
                        detail = f"{detail} {auth_hint}".strip() if detail else auth_hint
                    raise HomeAssistantError(f"Tater tool call failed ({resp.status}): {detail}")
                # Return value is not used by automations directly, but shows in traces/logs
                try:
                    return json.loads(text) if text else {"ok": True}
                except Exception:
                    return {"ok": True, "raw": text}
        except asyncio.TimeoutError as e:
            raise HomeAssistantError("Tater tool call timed out") from e
        except Exception as e:
            raise HomeAssistantError(f"Tater tool call error: {e}") from e

    def _make_service_handler(service_name: str):
        async def _service_handler(call: ServiceCall):
            if service_name == SERVICE_CALL_TOOL:
                tool = (call.data.get("tool") or "").strip()
                if not tool:
                    raise HomeAssistantError("Missing required field: tool")
                arguments = _build_arguments(call, tool, include_raw_arguments=True)
            else:
                tool = SERVICE_FIXED_TOOL[service_name]
                arguments = _build_arguments(call, tool, include_raw_arguments=False)

            return await _post_tool(tool, arguments)

        return _service_handler

    for service_name in REGISTERED_SERVICES:
        hass.services.async_register(DOMAIN, service_name, _make_service_handler(service_name))

    return True

async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    for service_name in REGISTERED_SERVICES:
        hass.services.async_remove(DOMAIN, service_name)
    return True
