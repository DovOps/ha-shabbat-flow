"""Rehearsal-only native power commands and setting-preservation evidence."""
from copy import deepcopy
import math
from homeassistant.components.fan import FanEntityFeature
from .ownership import instant

CLIMATE_SETTINGS=('temperature','target_temp_low','target_temp_high','fan_mode','preset_mode','swing_mode','swing_horizontal_mode')
FAN_SETTINGS=('percentage','preset_mode','direction','oscillating')
MODES={'heat','cool','heat_cool','auto','dry','fan_only'}


def snapshot(state):
    if state is None:return {'state':'unknown','context_id':None,'settings':{}}
    fields=CLIMATE_SETTINGS if state.domain=='climate' else FAN_SETTINGS if state.domain=='fan' else ()
    settings={k:state.attributes[k] for k in fields if isinstance(state.attributes.get(k),(str,bool)) or type(state.attributes.get(k)) in (int,float) and math.isfinite(state.attributes[k])}
    return {'state':state.state,'context_id':state.context.id,'settings':settings}


def power(value,domain):
    return ('on' if value in MODES else value) if domain=='climate' else value


def active_baseline(state,target,now):
    snap=snapshot(state);domain=target['entity_id'].split('.')[0]
    if power(snap['state'],domain)!='on':raise ValueError('rehearsal_capture_on')
    return {'target':deepcopy(target),'at':now.isoformat(),**snap}


def eligible(hass,target,baseline,now,wanted):
    """Return review contract, or an explicit reason. Never issue service calls."""
    state=hass.states.get(target['entity_id']);domain=target['entity_id'].split('.')[0];before=snapshot(state)
    if not state or state.state in ('unknown','unavailable') or state.attributes.get('restored'):return None,'execute_unavailable'
    active=before if power(before['state'],domain)=='on' else None
    if active is None and baseline and baseline['target']==target and 0<=(now-instant(baseline['at'])).total_seconds()<=90*86400:active=baseline
    if domain=='climate':
        modes=state.attributes.get('hvac_modes',[])
        if not hass.services.has_service('climate','set_hvac_mode') or 'off' not in modes:return None,'execute_service'
        if not any(type(before['settings'].get(k)) in (int,float) for k in ('temperature','target_temp_low','target_temp_high')):return None,'rehearsal_settings_unknown'
        mode=active['state'] if active else None
        if wanted=='on' and (mode not in MODES or mode not in modes):return None,'rehearsal_capture_on'
        return {'domain':domain,'mode':mode,'settings':before['settings'],'baseline_at':baseline['at'] if active is baseline else None},None
    if domain=='fan':
        features=state.attributes.get('supported_features',0)
        if any(not hass.services.has_service('fan',s) for s in ('turn_on','turn_off')) or not features & FanEntityFeature.TURN_ON or not features & FanEntityFeature.TURN_OFF:return None,'execute_service'
        if wanted=='on' and not active:return None,'rehearsal_capture_on'
        settings=deepcopy(active['settings'] if active else before['settings'])
        if wanted=='on' and features & FanEntityFeature.SET_SPEED and not (type(settings.get('percentage')) in (int,float) and 0<settings['percentage']<=100):return None,'rehearsal_settings_unknown'
        preset=settings.get('preset_mode')
        if wanted=='on' and preset and (not features & FanEntityFeature.PRESET_MODE or preset not in state.attributes.get('preset_modes',[])):return None,'rehearsal_settings_unknown'
        return {'domain':domain,'settings':settings,'speed':bool(features & FanEntityFeature.SET_SPEED),'preset':bool(features & FanEntityFeature.PRESET_MODE),'baseline_at':baseline['at'] if active is baseline else None},None
    return {'domain':domain,'settings':{}},None


def command(contract,wanted,entity):
    domain=contract['domain'];data={'entity_id':entity}
    if domain=='climate':return domain,'set_hvac_mode',{**data,'hvac_mode':contract['mode'] if wanted=='on' else 'off'}
    if domain=='fan' and wanted=='on':
        settings=contract['settings']
        if contract['preset'] and settings.get('preset_mode'):data['preset_mode']=settings['preset_mode']
        elif contract['speed']:data['percentage']=settings['percentage']
    return domain,'turn_'+wanted,data


def matches(contract,wanted,state):
    if state is None or power(state.state,contract['domain'])!=wanted:return False
    current=snapshot(state)['settings'];expected=contract['settings']
    if contract['domain']=='climate':
        return (wanted=='off' or state.state==contract['mode']) and all(current.get(k)==v for k,v in expected.items())
    if contract['domain']=='fan':
        # Off commonly publishes zero speed / clears the active preset. Direction
        # and oscillation still matter; On must restore the reviewed active settings.
        keys=expected if wanted=='on' else set(expected)-{'percentage','preset_mode'}
        return all(current.get(k)==expected[k] for k in keys)
    return True
