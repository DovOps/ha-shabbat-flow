"""Bounded authenticated preview API; no service/device/recorder operations."""
from datetime import datetime, timezone
import json
from zoneinfo import ZoneInfo
from aiohttp import web
from homeassistant.helpers.http import HomeAssistantView
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, CALENDAR_FIELDS
from .engine.compiler import PlanError
from .engine.schedule import compile_schedule

MAX_BODY = 128 * 1024


def invalid_constant(_):
    raise ValueError("invalid_request")


class BaseView(HomeAssistantView):
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    def check(self, request):
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            raise web.HTTPForbidden()
        if "entry" not in self.hass.data.get(DOMAIN, {}):
            raise web.HTTPServiceUnavailable()

    def response(self, value, status=200):
        return web.json_response(value, status=status, headers={"Cache-Control": "no-store"})


class SampleView(BaseView):
    url = "/api/shabbat_flow/sample"
    name = "api:shabbat_flow:sample"

    async def get(self, request):
        self.check(request)
        return self.response(self.hass.data[DOMAIN]["sample"])


class CatalogView(BaseView):
    url = "/api/shabbat_flow/catalog"
    name = "api:shabbat_flow:catalog"

    async def get(self, request):
        self.check(request)
        return self.response(self.hass.data[DOMAIN]["catalogs"])


class PreviewView(BaseView):
    url = "/api/shabbat_flow/preview"
    name = "api:shabbat_flow:preview"

    async def post(self, request):
        self.check(request)
        if request.content_type != "application/json":
            return self.response({"error": "invalid_request"}, 400)
        if request.content_length is not None and request.content_length > MAX_BODY:
            return self.response({"error": "too_large"}, 413)
        body = bytearray()
        async for chunk in request.content.iter_chunked(16384):
            body.extend(chunk)
            if len(body) > MAX_BODY:
                return self.response({"error": "too_large"}, 413)
        try:
            payload = json.loads(body, parse_constant=invalid_constant)
            if type(payload) is not dict or set(payload) != {"config", "plan"}:
                raise ValueError("invalid_request")
            result = await self.hass.async_add_executor_job(compile_schedule, payload["config"], payload["plan"])
        except PlanError as exc:
            return self.response({"error": exc.code}, 400)
        except (ValueError, TypeError, UnicodeDecodeError, RecursionError, OverflowError):
            return self.response({"error": "invalid_request"}, 400)
        return self.response(result)


class CalendarView(BaseView):
    url = "/api/shabbat_flow/calendar"
    name = "api:shabbat_flow:calendar"

    async def get(self, request):
        self.check(request)
        entry = self.hass.data[DOMAIN]["entry"]
        zone = ZoneInfo(self.hass.config.time_zone)
        mode = entry.options.get("source_mode", "jewish_calendar")
        if mode == "manual":
            return self.response({"source": "manual", "timezone": str(zone), "values": {}, "coverage": "manual_only"})
        registry = er.async_get(self.hass)
        provider_present = bool(self.hass.config_entries.async_entries("jewish_calendar"))
        expected = {"candle_lighting": {"upcoming_candle_lighting"}, "sunrise": {"netz_hachama", "hanetz_hachama"},
                    "end": {"upcoming_havdalah"}, "active": {"issur_melacha_in_effect"}}
        values = {}
        for field in CALENDAR_FIELDS:
            entity_id = entry.options.get(field)
            if not entity_id and mode == "jewish_calendar":
                candidates = [e.entity_id for e in registry.entities.values()
                              if e.platform == "jewish_calendar" and e.disabled_by is None
                              and e.translation_key in expected[field]]
                if len(candidates) == 1:
                    entity_id = candidates[0]
                elif len(candidates) > 1:
                    values[field] = {"status": "ambiguous"}
                    continue
            if not entity_id:
                values[field] = {"status": "not_configured"}
                continue
            state = self.hass.states.get(entity_id)
            item = {"entity_id": entity_id, "status": "unavailable"}
            if state is not None:
                item["last_updated"] = state.last_updated.isoformat()
                if field == "active":
                    item["status"] = state.state if state.state in ("on", "off", "unknown", "unavailable") else "unknown"
                elif state.state in ("unknown", "unavailable"):
                    item["status"] = state.state
                else:
                    try:
                        value = datetime.fromisoformat(state.state)
                        if value.tzinfo is None or value.utcoffset() is None or value.microsecond:
                            raise ValueError("requires_explicit_time")
                        item.update(status="available", value=value.astimezone(zone).isoformat())
                    except (ValueError, OverflowError):
                        item["status"] = "invalid_time"
            values[field] = item
        return self.response({"source": mode, "provider_present": provider_present, "timezone": str(zone),
                              "observed_at": datetime.now(timezone.utc).isoformat(),
                              "coverage": "selected_values_only", "values": values})
