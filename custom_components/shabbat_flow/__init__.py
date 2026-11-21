"""Home Assistant host for a non-executing ShabbatFlow sample."""
import json
from asyncio import Lock
from homeassistant.helpers.storage import Store
from .household import empty_settings, migrate_settings
from pathlib import Path
from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from .const import DOMAIN, PANEL, STATIC, VERSION
from .api import PreviewView, SampleView, CatalogView, CalendarView, HouseholdView, HouseholdPlanView, UpcomingView, ObserveView, PdfView

ROOT = Path(__file__).parent


def load_assets():
    sample = json.loads((ROOT / "fixtures/period-preview.json").read_text())
    base = json.loads((ROOT / "www/i18n.json").read_text())
    extra = json.loads((ROOT / "www/period-i18n.json").read_text())
    return sample, {lang: {**base[lang], **extra[lang]} for lang in base}


async def async_setup_entry(hass, entry):
    if getattr(entry, "title", None) == "ShabbatFlow Preview":
        hass.config_entries.async_update_entry(entry, title="Shabbat Flow")
    data = hass.data.setdefault(DOMAIN, {})
    if "household" not in data:
        data["household_store"] = Store(hass, 1, DOMAIN + ".household")
        data["household"] = migrate_settings(await data["household_store"].async_load() or empty_settings())
        data["household_lock"] = Lock()
    from .notifications import Notifications
    if 'notifications' not in data or data['notifications'].closed:
        data['notifications']=Notifications(hass)
        await data['notifications'].load()
    from .observe import Observer
    if "observer" not in data or data["observer"].closed:
        data["observer"] = Observer(hass)
        await data["observer"].load()
    from .pdf_store import PdfStore
    data["pdf"] = PdfStore(hass)
    await data["pdf"].tidy()
    if not data.get("registered"):
        sample, catalogs = await hass.async_add_executor_job(load_assets)
        await hass.http.async_register_static_paths([StaticPathConfig(STATIC, str(ROOT / "www"), False)])
        for view in (PreviewView, SampleView, CatalogView, CalendarView, HouseholdView, HouseholdPlanView, UpcomingView, ObserveView, PdfView):
            hass.http.register_view(view(hass))
        data.update(registered=True, sample=sample, catalogs=catalogs)
    data["entry"] = entry
    try:
        await panel_custom.async_register_panel(
            hass, frontend_url_path=PANEL, webcomponent_name="shabbat-flow-panel",
            sidebar_title="Shabbat Flow", sidebar_icon="mdi:candle",
            module_url=f"{STATIC}/panel.js?v={VERSION}", require_admin=True,
        )
    except Exception:
        data.pop("entry", None)
        raise
    entry.async_on_unload(entry.add_update_listener(async_options_updated))
    return True


async def async_options_updated(hass, entry):
    # Read options at request time; never restart devices or alter their state.
    hass.data[DOMAIN]["entry"] = entry


async def async_unload_entry(hass, entry):
    observer = hass.data.get(DOMAIN, {}).get("observer")
    if observer: observer.close()
    pdf=hass.data.get(DOMAIN,{}).get("pdf")
    if pdf: await pdf.close()
    notifications=hass.data.get(DOMAIN,{}).get('notifications')
    if notifications:notifications.close()
    frontend.async_remove_panel(hass, PANEL)
    hass.data.get(DOMAIN, {}).pop("entry", None)
    return True
