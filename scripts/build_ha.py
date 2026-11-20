"""Reproducibly assemble generated HA assets and an installable ZIP."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'custom_components/shabbat_flow'


def generated():
    files = {}
    for name in ('compiler.py', 'planning.py', 'schedule.py'):
        files['engine/'+name] = (ROOT/'src/shabbat_flow'/name).read_bytes()
    files['engine/__init__.py'] = b'"""Generated pure planner engine; edit src/shabbat_flow instead."""\n'
    web = ROOT/'src/shabbat_flow/web'
    for name in ('period.mjs','thermal-report.mjs','observe.mjs','hvac-map.mjs','lighting-map.mjs','period-report.mjs','period-model.mjs','model.mjs','style.css','i18n.json','period-i18n.json','household.mjs','household-model.mjs','household-i18n.json','tips.html'):
        files['www/'+name] = (web/name).read_bytes()
    html = (web/'period.html').read_text()
    for name in ('style.css','period.mjs','logo.png'):
        html = html.replace('"/'+name+'"', '"./'+name+'"')
    html = html.replace('href="/"', 'href="./period.html"')
    html = html.replace('<p><a href="./period.html" data-i18n="original_preview"></a></p>', '')
    html = html.replace('<p id="status"', '<p><a href="./household.html" data-i18n="house_setup"></a></p><p id="status"')
    files['www/period.html'] = html.encode()
    files['www/household.html'] = (web/'household.html').read_bytes()
    files['www/transport.mjs'] = (ROOT/'src/shabbat_flow/ha_transport.mjs').read_bytes()
    files['www/panel.js'] = (ROOT/'src/shabbat_flow/ha_panel.js').read_bytes()
    files['www/logo.png'] = (ROOT/'assets/logo.png').read_bytes()
    files['fixtures/period-preview.json'] = (ROOT/'examples/period-preview.json').read_bytes()
    return files


def build(check=False):
    expected = generated()
    for name, data in expected.items():
        path = TARGET/name
        if check:
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit('Generated HA asset drift: '+name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    actual = {str(p.relative_to(TARGET)) for directory in ('engine','www','fixtures')
              for p in (TARGET/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual != set(expected):
        raise SystemExit('Unexpected generated HA assets: '+str(sorted(actual-set(expected))))


def archive():
    version = json.loads((TARGET/'manifest.json').read_text())['version']
    output = ROOT/'dist'/f'shabbat-flow-{version}.zip'
    output.parent.mkdir(exist_ok=True)
    # Exact source allowlist plus generated assets: no logs/private/temp files.
    names = set(generated()) | {'__init__.py','api.py','observe.py','thermal.py','ownership.py','upcoming.py','household.py','const.py','config_flow.py','manifest.json','strings.json','translations/en.json','translations/he.json'}
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            info = zipfile.ZipInfo('custom_components/shabbat_flow/'+name, date_time=(2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info,(TARGET/name).read_bytes())
    checksum = sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(checksum+'  '+output.name+'\n')
    print(str(output.relative_to(ROOT)), checksum)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--zip',action='store_true');args=parser.parse_args()
    build(args.check)
    if args.zip: archive()
