"""Pure, deterministic preview compiler. No HA imports, I/O or device calls."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
ROLES = {'entry','nightlights','bedroom_hall','living_spots','dining','background','kitchen_spots','island','shared_hvac'}
ERROR_CODES = {'invalid_schema','invalid_mapping','invalid_timezone','invalid_time','unsupported_period','away_conflict','invalid_sequence','event_conflict'}
RULES = {'entry_ready','entry_end','room_ready','shared_ready','night_path','hall_off','dinner_lights','dinner_hvac_start','shared_hvac_stop','bedroom_hvac_start','bedroom_lights_off','night_change','dawn_off','kitchen_morning','living_morning','lunch_lights'}


class PlanError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code='invalid_schema'):
    if not ok:
        raise PlanError(code)


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected))


def identifier(value):
    require(isinstance(value,str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value) is not None)


def labels(value):
    keys(value, {'en','he'})
    require(all(isinstance(v,str) and 0<len(v.strip())<=100 for v in value.values()))


def references(value, valid):
    require(type(value) is list and len(value)<=100)
    require(all(isinstance(v,str) for v in value))
    require(len(value)==len(set(value)))
    require(all(v in valid for v in value), 'invalid_mapping')


def validate_config(config):
    keys(config, {'schema_version','rooms','loads','dependencies','roles'})
    require(type(config['schema_version']) is int and config['schema_version']==1)
    for field in ('rooms','loads'):
        require(type(config[field]) is dict and 1<=len(config[field])<=100)
        for key in config[field]:
            identifier(key)
    for value in config['loads'].values():
        labels(value)
    for room in config['rooms'].values():
        keys(room, {'label','wall','climate','sleep_lights'})
        labels(room['label'])
        references(room['sleep_lights'],config['loads'])
        for field in ('wall','climate'):
            require(isinstance(room[field],str) and room[field] in config['loads'],'invalid_mapping')
    require(type(config['dependencies']) is list and len(config['dependencies'])<=100)
    for dependency in config['dependencies']:
        keys(dependency, {'rooms','loads'})
        references(dependency['rooms'], config['rooms'])
        references(dependency['loads'], config['loads'])
        require(bool(dependency['rooms']) and bool(dependency['loads']))
    protected={load for dep in config['dependencies'] for load in dep['loads']}
    for room in config['rooms'].values():
        require(not (set(room['sleep_lights']) & protected),'invalid_mapping')
    keys(config['roles'], ROLES)
    for value in config['roles'].values():
        references(value, config['loads'])


def parse_instant(value, zone):
    require(isinstance(value,str) and len(value)<=40, 'invalid_time')
    try:
        result=datetime.fromisoformat(value)
    except ValueError:
        raise PlanError('invalid_time') from None
    require(result.tzinfo is not None and result.utcoffset() is not None,'invalid_time')
    local=result.astimezone(zone)
    # Reject supplied offsets inconsistent with the zone, including imaginary wall times.
    require(result.utcoffset()==local.utcoffset() and result.replace(tzinfo=None)==local.replace(tzinfo=None),'invalid_time')
    require(result.second==0 and result.microsecond==0,'invalid_time')
    return result.astimezone(UTC)


def validate_plan(config, plan):
    keys(plan, {'schema_version','language','timezone','candle_lighting','sunrise','end','home','used_rooms','dinner','lunch','offsets'})
    require(type(plan['schema_version']) is int and plan['schema_version']==1)
    require(isinstance(plan['language'],str) and plan['language'] in ('en','he'))
    require(type(plan['home']) is bool)
    require(isinstance(plan['timezone'],str) and len(plan['timezone'])<=100,'invalid_timezone')
    try:
        zone=ZoneInfo(plan['timezone'])
    except (ZoneInfoNotFoundError,ValueError):
        raise PlanError('invalid_timezone') from None
    references(plan['used_rooms'], config['rooms'])
    require(all(isinstance(plan[k],str) and plan[k] in ('away','family','hosting') for k in ('dinner','lunch')))
    keys(plan['offsets'], {'bedroom_hvac','shared_hvac_off','night_lights','bedroom_lights'})
    require(all(type(v) is int and 0<=v<=720 for v in plan['offsets'].values()))
    candle,sunrise,end=(parse_instant(plan[k],zone) for k in ('candle_lighting','sunrise','end'))
    require(candle<sunrise<end,'invalid_sequence')
    day=candle.astimezone(zone).date()
    require(day.weekday()==4 and sunrise.astimezone(zone).date()==day+timedelta(days=1) and end.astimezone(zone).date()==day+timedelta(days=1),'unsupported_period')
    require(plan['home'] or (not plan['used_rooms'] and plan['dinner']=='away' and plan['lunch']=='away'),'away_conflict')
    return zone,candle,sunrise,end


def compile_plan(config, plan):
    validate_config(config)
    zone,candle,sunrise,end=validate_plan(config,plan)
    events={}
    preparation=candle-timedelta(minutes=30)
    day=candle.astimezone(zone).date()

    def clock(hour, minute=0):
        local=datetime.combine(day+timedelta(days=1), datetime.min.time()).replace(hour=hour,minute=minute,tzinfo=zone)
        return parse_instant(local.isoformat(),zone)

    def emit(loads, state, when, rule):
        require(preparation<=when<end,'invalid_sequence')
        for load in sorted(loads):
            key=(when,load)
            if key in events:
                require(events[key]['state']==state,'event_conflict')
                continue
            utc=when.isoformat().replace('+00:00','Z')
            event_id=sha256(f'{load}|{state}|{utc}|{rule}'.encode()).hexdigest()[:16]
            events[key]={'id':event_id,'load':load,'state':state,'utc':utc,'local':when.astimezone(zone).isoformat(),'rule':rule}

    def role(name,state,when,rule):
        emit(config['roles'][name],state,when,rule)

    if plan['home']:
        night=candle+timedelta(minutes=plan['offsets']['night_lights'])
        bedroom=candle+timedelta(minutes=plan['offsets']['bedroom_hvac'])
        bedroom_lights=candle+timedelta(minutes=plan['offsets']['bedroom_lights'])
        shared_off=candle+timedelta(minutes=plan['offsets']['shared_hvac_off'])
        dawn=sunrise-timedelta(hours=1)
        kitchen_morning=sunrise+timedelta(hours=2)
        require(candle<=night<dawn and candle<=bedroom<end,'invalid_sequence')
        role('entry','on',preparation,'entry_ready')
        role('entry','off',clock(0),'entry_end')
        role('nightlights','on',candle,'night_path')
        role('bedroom_hall','off',candle,'hall_off')
        for room_id in sorted(plan['used_rooms']):
            room=config['rooms'][room_id]
            emit([room['wall']],'on',preparation,'room_ready')
            emit([room['climate']],'on',bedroom,'bedroom_hvac_start')
            emit(room['sleep_lights'],'off',bedroom_lights,'bedroom_lights_off')
        for dependency in config['dependencies']:
            if set(dependency['rooms']) & set(plan['used_rooms']):
                emit(dependency['loads'],'on',preparation,'shared_ready')
        if plan['dinner']!='away':
            for name in ('living_spots','dining','kitchen_spots'):
                role(name,'on',preparation,'dinner_lights')
            dinner_ac=candle+timedelta(minutes=100)
            require(dinner_ac<shared_off<end,'invalid_sequence')
            role('shared_hvac','on',dinner_ac,'dinner_hvac_start')
            role('shared_hvac','off',shared_off,'shared_hvac_stop')
        for name in ('living_spots','dining','kitchen_spots'):
            role(name,'off',night,'night_change')
        for name in ('background','island'):
            role(name,'on',night,'night_change')
        for name in ('background','nightlights'):
            role(name,'off',dawn,'dawn_off')
        role('island','off',kitchen_morning,'kitchen_morning')
        role('kitchen_spots','on',kitchen_morning,'kitchen_morning')
        role('living_spots','on',clock(8),'living_morning')
        if plan['lunch']!='away':
            role('dining','on',clock(10,30),'lunch_lights')
    normalized={k:v for k,v in plan.items() if k!='language'}
    digest=sha256(json.dumps({'config':config,'plan':normalized,'compiler':1},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    return {'preview_only':True,'digest':digest,'preparation_at':preparation.astimezone(zone).isoformat(),'events':[v for _,v in sorted(events.items())]}
