"""Loopback development harness, not a production HA integration."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys

from .compiler import compile_plan, PlanError
from .schedule import compile_schedule

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).parent / 'web'
MAX_BODY = 128 * 1024
STATIC = {'/':('index.html','text/html'),'/app.mjs':('app.mjs','text/javascript'),'/model.mjs':('model.mjs','text/javascript'),'/style.css':('style.css','text/css')}

STATIC['/transport.mjs']=('transport.mjs','text/javascript')
STATIC.update({'/hvac-map.mjs': ('hvac-map.mjs', 'text/javascript'), '/lighting-map.mjs': ('lighting-map.mjs', 'text/javascript'), '/period-report.mjs': ('period-report.mjs', 'text/javascript'), '/v2': ('period.html', 'text/html'), '/period.mjs': ('period.mjs', 'text/javascript'), '/period-model.mjs': ('period-model.mjs', 'text/javascript')})

def reject_constant(_):
    raise ValueError('invalid_json')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log request bodies, query strings or input values.

    def reply(self, status, data, content_type='application/json'):
        body=json.dumps(data,ensure_ascii=False).encode() if content_type=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',content_type if content_type.startswith('image/') else content_type+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def permitted(self):
        host=f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host')!=host or self.headers.get('Origin',f'http://{host}')!=f'http://{host}':
            self.reply(403,{'error':'forbidden'})
            return False
        return True

    def do_GET(self):
        if not self.permitted():
            return
        if self.path in STATIC:
            filename,mime=STATIC[self.path]
            self.reply(200,(WEB/filename).read_bytes(),mime)
        elif self.path=='/logo.png':
            self.reply(200,(ROOT/'assets/logo.png').read_bytes(),'image/png')
        elif self.path=='/api/i18n':
            self.reply(200,json.loads((WEB/'i18n.json').read_text()))
        elif self.path=='/api/v2/i18n':
            base=json.loads((WEB/'i18n.json').read_text())
            extra=json.loads((WEB/'period-i18n.json').read_text())
            self.reply(200,{lang: {**base[lang], **extra[lang]} for lang in base})
        elif self.path=='/api/v2/calendar':
            self.reply(200,{'source':'standalone','values':{},'coverage':'manual_only'})
        elif self.path=='/api/v2/example':
            self.reply(200,json.loads((ROOT/'examples/period-preview.json').read_text()))
        elif self.path=='/api/example':
            self.reply(200,{'config':json.loads((ROOT/'examples/household.json').read_text()),'plan':json.loads((ROOT/'examples/plan.json').read_text())})
        else:
            self.reply(404,{'error':'not_found'})

    def do_POST(self):
        if not self.permitted():
            return
        if self.path not in ('/api/preview','/api/v2/preview'):
            self.reply(404,{'error':'not_found'})
            return
        try:
            length=int(self.headers.get('Content-Length','-1'))
            if length>MAX_BODY:
                self.reply(413,{'error':'too_large'})
                return
            if length<0 or self.headers.get('Content-Type')!='application/json' or self.headers.get('Transfer-Encoding'):
                raise ValueError('invalid_request')
            payload=json.loads(self.rfile.read(length),parse_constant=reject_constant)
            if type(payload) is not dict or set(payload)!={'config','plan'}:
                raise ValueError('invalid_request')
            compiler=compile_schedule if self.path=='/api/v2/preview' else compile_plan
            result=compiler(payload['config'],payload['plan'])
        except PlanError as exc:
            self.reply(400,{'error':exc.code})
        except (ValueError,TypeError,UnicodeDecodeError,RecursionError):
            self.reply(400,{'error':'invalid_request'})
        else:
            self.reply(200,result)


def main():
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8765
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'ShabbatFlow preview: http://127.0.0.1:{server.server_port}',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__=='__main__':
    main()
