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


async def read_body(request):
    if request.content_type != "application/json":
        raise ValueError("invalid_request")
    if request.content_length is not None and request.content_length > MAX_BODY:
        raise web.HTTPRequestEntityTooLarge(max_size=MAX_BODY, actual_size=request.content_length)
    body = bytearray()
    async for chunk in request.content.iter_chunked(16384):
        body.extend(chunk)
        if len(body) > MAX_BODY:
            raise web.HTTPRequestEntityTooLarge(max_size=MAX_BODY, actual_size=len(body))
    value = json.loads(body, parse_constant=invalid_constant)
    if type(value) is not dict:
        raise ValueError("invalid_request")
    return value


class HouseholdView(BaseView):
    url = "/api/shabbat_flow/household"
    name = "api:shabbat_flow:household"

    async def get(self, request):
        from .household import inventory, issues
        self.check(request)
        inv = inventory(self.hass)
        saved = self.hass.data[DOMAIN]["household"]
        return self.response({"inventory": inv, "settings": saved, "issues": issues(saved, inv),
                              "observed_at": datetime.now(timezone.utc).isoformat()})

    async def post(self, request):
        from .household import inventory, validate_settings, validate_label_filters, empty_label_filters
        self.check(request)
        try:
            payload = await read_body(request)
            if not {"revision", "inventory_revision", "rooms"} <= set(payload) or not set(payload) <= {"revision", "inventory_revision", "rooms", "label_filters", "post_shutoff"} or type(payload["revision"]) is not int:
                raise ValueError("invalid_request")
            data = self.hass.data[DOMAIN]
            async with data["household_lock"]:
                inv = inventory(self.hass)
                if payload["revision"] != data["household"]["revision"] or payload["inventory_revision"] != inv["revision"]:
                    return self.response({"error": "stale_household"}, 409)
                bindings = validate_settings(payload["rooms"], inv)
                previous_filters = data["household"].get("label_filters", empty_label_filters())
                filters = validate_label_filters(payload.get("label_filters", previous_filters), inv, previous_filters)
                post_shutoff = payload.get("post_shutoff", data["household"].get("post_shutoff", False))
                if type(post_shutoff) is not bool: raise ValueError("invalid_request")
                saved = {"post_shutoff": post_shutoff, "label_filters": filters, "schema_version": 2, "revision": payload["revision"] + 1, "rooms": payload["rooms"], "bindings": bindings}
                await data["household_store"].async_save(saved)
                data["household"] = saved
        except PlanError as exc:
            return self.response({"error": exc.code}, 400)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, RecursionError):
            return self.response({"error": "invalid_request"}, 400)
        except OSError:
            return self.response({"error": "storage_failed"}, 500)
        return await self.get(request)


class HouseholdPlanView(BaseView):
    url = "/api/shabbat_flow/household_plan"
    name = "api:shabbat_flow:household_plan"

    async def post(self, request):
        from .household import inventory, workspace
        self.check(request)
        try:
            payload = await read_body(request)
            if set(payload) != {"revision", "inventory_revision", "snapshot"}:
                raise ValueError("invalid_request")
            saved = self.hass.data[DOMAIN]["household"]
            inv = inventory(self.hass)
            if payload["revision"] != saved["revision"] or payload["inventory_revision"] != inv["revision"]:
                return self.response({"error": "stale_household"}, 409)
            result = workspace(saved, inv, payload["snapshot"])
        except PlanError as exc:
            return self.response({"error": exc.code}, 400)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, RecursionError):
            return self.response({"error": "invalid_request"}, 400)
        return self.response(result)


class UpcomingView(BaseView):
    url = "/api/shabbat_flow/upcoming"
    name = "api:shabbat_flow:upcoming"

    async def get(self, request):
        from .upcoming import upcoming
        self.check(request)
        if self.hass.data[DOMAIN]["entry"].options.get("source_mode") == "manual":
            return self.response({"status": "unavailable", "error": "calendar_manual"})
        try:
            return self.response(await upcoming(self.hass))
        except PlanError as exc:
            code = exc.code if exc.code.startswith("calendar_") else "calendar_incomplete"
            return self.response({"status": "unavailable", "error": code})


class ObserveView(BaseView):
    url = '/api/shabbat_flow/observe'
    name = 'api:shabbat_flow:observe'

    async def get(self, request):
        self.check(request)
        return self.response(self.hass.data[DOMAIN]['observer'].listing())

    async def post(self, request):
        self.check(request)
        from .ownership import forecast_ha, ownership_report
        from .observe import resolve_mapping
        try:
            payload = await read_body(request)
            observer = self.hass.data[DOMAIN]['observer']
            op = payload.get('op')
            if op in ('start','forecast'):
                allowed = {'op','bundle','policy','request_id'} if op == 'start' else {'op','bundle'}
                if set(payload) != allowed and not (op == 'start' and set(payload) == allowed | {'weather_entity_id'}): raise ValueError('invalid_request')
                bundle = payload['bundle']
                if not isinstance(bundle,dict) or set(bundle) != {'config','plan'}: raise ValueError('invalid_request')
                if op == 'start':
                    run = await observer.start(bundle,payload['policy'],payload['request_id'],getattr(request['hass_user'],'id',None),weather_entity_id=payload.get('weather_entity_id'))
                    return self.response({'id':run['id'],'status':run['status'],'mode':'observe'})
                preview = await self.hass.async_add_executor_job(compile_schedule,bundle['config'],bundle['plan'])
                overlay = forecast_ha(self.hass,bundle['plan']['snapshot'])
                mapping, unresolved = resolve_mapping(self.hass,bundle)
                return self.response({'overlay':overlay,'ownership':ownership_report(preview['events'],mapping,overlay),'unmapped':unresolved})
            if op == 'configure' and set(payload)=={'op','id','policy'} and isinstance(payload['id'],str):
                return self.response(await observer.configure(payload['id'],payload['policy']))
            if op in ('stop','export') and set(payload)=={'op','id'} and isinstance(payload['id'],str):
                result = await observer.stop(payload['id']) if op=='stop' else observer.export(payload['id'])
                return self.response(result)
            raise ValueError('invalid_request')
        except PlanError as exc:
            return self.response({'error':exc.code},400)
        except (ValueError,TypeError,KeyError,UnicodeDecodeError,RecursionError) as exc:
            code=str(exc) if str(exc).startswith('observe_') else 'invalid_request'
            return self.response({'error':code},409 if code=='observe_conflict' else 400)
