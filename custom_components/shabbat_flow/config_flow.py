"""Setup a preview panel; optional calendar entities are read-only inputs."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, CALENDAR_FIELDS


def schema(options):
    fields = {vol.Required("source_mode", default=options.get("source_mode", "jewish_calendar")): selector.SelectSelector(selector.SelectSelectorConfig(options=["jewish_calendar", "selected_entities", "manual"], translation_key="source_mode"))}
    for key in CALENDAR_FIELDS:
        marker = vol.Optional(key, description={"suggested_value": options.get(key, "")})
        domains = ["binary_sensor"] if key == "active" else ["sensor", "input_datetime"]
        fields[marker] = selector.EntitySelector(selector.EntitySelectorConfig(domain=domains))
    return vol.Schema(fields)


class ShabbatFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Shabbat Flow", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ShabbatFlowOptionsFlow()


class ShabbatFlowOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data={k: v for k, v in user_input.items()
                                                           if k in (*CALENDAR_FIELDS, "source_mode") and v})
        return self.async_show_form(step_id="init", data_schema=schema(self.config_entry.options))
