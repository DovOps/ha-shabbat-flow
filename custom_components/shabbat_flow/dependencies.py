"""Read-only capability status; detection never installs or configures providers."""
from homeassistant.helpers import entity_registry as er, area_registry as ar, label_registry as lr
from .notifications import capability


def discover(hass):
    entities=list(er.async_get(hass).entities.values())
    def usable(e):
        s=hass.states.get(e.entity_id)
        return e.disabled_by is None and s is not None and s.state not in ('unknown','unavailable')
    def row(id,requirement,found,ready,hint):
        return {'id':id,'requirement':requirement,'detected':found,'ready':ready,'status':'ready' if ready else 'needs_setup' if found else 'missing','hint':hint}
    entries=hass.config_entries.async_entries('jewish_calendar')
    calendar=[e for e in entities if e.platform=='jewish_calendar' and e.domain=='calendar' and e.translation_key in ('daily_events','yearly_events')]
    good=bool(len(entries)==1 and all(len([e for e in calendar if e.config_entry_id==entries[0].entry_id and e.translation_key==key and usable(e)])==1 for key in ('daily_events','yearly_events')) and hass.services.has_service('calendar','get_events'))
    manual=hass.data['shabbat_flow']['entry'].options.get('source_mode')=='manual'
    climate=[e for e in entities if e.domain=='climate'];weather=hass.states.async_all('weather')
    thermal=[s for s in hass.states.async_all('sensor') if s.attributes.get('device_class')=='temperature']
    issur=[e for e in entities if e.platform=='jewish_calendar' and e.translation_key=='issur_melacha_in_effect']
    from .ownership import automation_sources
    # Automation introspection is best-effort; don't claim all triggers predictable.
    try: configs,_=automation_sources(hass);automation_ready=any(c['config'] is not None for c in configs)
    except Exception:automation_ready=False
    cap=capability(hass)
    rows=[row('core','required',True,True,'core'),
          row('areas','required_for_rooms',bool(ar.async_get(hass).areas),bool(ar.async_get(hass).areas),'areas'),
          row('calendar','preferred',bool(entries),good,'calendar_manual' if manual else 'calendar'),
          row('twilio','optional',bool(hass.data.get('twilio_sms_ui')),cap['available'],'twilio'),
          row('push','optional',bool(hass.data.get('mobile_app')),cap['push_available'],'push'),
          row('external_url','optional',cap['report_url_available'],cap['report_url_available'],'external_url'),
          row('climate','required_for_climate',bool(climate),any(usable(e) for e in climate),'climate'),
          row('weather','optional',bool(weather),any(s.state not in ('unknown','unavailable') and isinstance(s.attributes.get('temperature'),(int,float)) for s in weather),'weather'),
          row('temperature','optional',bool(thermal),any(s.state not in ('unknown','unavailable') for s in thermal),'temperature'),
          row('labels','optional',bool(lr.async_get(hass).labels),bool(lr.async_get(hass).labels),'labels'),
          row('automations','optional',bool(hass.data.get('automation')),automation_ready,'automations'),
          row('issur','optional',bool(issur),any(usable(e) for e in issur),'issur')]
    return {'dependencies':rows,'calendar_mode':'manual' if manual else 'automatic'}
