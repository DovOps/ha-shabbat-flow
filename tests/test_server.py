import http.client
import json
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
from shabbat_flow.server import Handler, MAX_BODY
from shabbat_flow.compiler import ERROR_CODES, RULES

ROOT=Path(__file__).resolve().parents[1]


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def request(self,method,path,body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        connection.request(method,path,body=body,headers=headers or {})
        response=connection.getresponse();data=response.read();status=response.status
        connection.close();return status,data

    def test_fixture_preview_contract(self):
        status,data=self.request('GET','/api/example')
        self.assertEqual(status,200)
        status,data=self.request('POST','/api/preview',data,{'Content-Type':'application/json'})
        self.assertEqual(status,200)
        self.assertTrue(json.loads(data)['preview_only'])

    def test_v2_preview_and_static_contract(self):
        status, data = self.request('GET', '/api/v2/example')
        self.assertEqual(status, 200)
        status, result = self.request('POST', '/api/v2/preview', data, {'Content-Type': 'application/json'})
        self.assertEqual(status, 200)
        result = json.loads(result)
        self.assertTrue(result['complete'] and result['preview_only'])
        self.assertTrue(result['events'])
        for path in ('/v2', '/period.mjs', '/period-model.mjs', '/api/v2/i18n', '/logo.png'):
            self.assertEqual(self.request('GET', path)[0], 200)
        self.assertEqual(self.request('POST', '/api/v2/activate', '{}', {'Content-Type': 'application/json'})[0], 404)

    def test_v2_isolation_validation_and_origin(self):
        data = self.request('GET', '/api/v2/example')[1]
        headers = {'Content-Type': 'application/json'}
        self.assertEqual(self.request('POST', '/api/preview', data, headers)[0], 400)
        old = self.request('GET', '/api/example')[1]
        self.assertEqual(self.request('POST', '/api/v2/preview', old, headers)[0], 400)
        headers['Origin'] = 'https://evil.example'
        self.assertEqual(self.request('POST', '/api/v2/preview', data, headers)[0], 403)

    def test_wrong_origin_and_host(self):
        for headers in ({'Host':'evil.example'},{'Origin':'https://evil.example'}):
            self.assertEqual(self.request('GET','/api/example',headers=headers)[0],403)

    def test_limits_and_malformed(self):
        self.assertEqual(self.request('POST','/api/preview','x'*(MAX_BODY+1),{'Content-Type':'application/json'})[0],413)
        for value in ['null','[]','{','{"config":NaN,"plan":{}}']:
            self.assertEqual(self.request('POST','/api/preview',value,{'Content-Type':'application/json'})[0],400)

    def test_no_arbitrary_files_or_execution_endpoint(self):
        for path in ['/../examples/plan.json','/api/activate','/.git/config','/api/token']:
            self.assertEqual(self.request('GET',path)[0],404)
        self.assertEqual(self.request('POST','/api/activate','{}',{'Content-Type':'application/json'})[0],404)

    def test_translation_coverage(self):
        data=json.loads(self.request('GET','/api/i18n')[1])
        for language in ('en','he'):
            for key in ERROR_CODES:self.assertIn('error_'+key,data[language])
            for key in RULES:self.assertIn('rule_'+key,data[language])


if __name__=='__main__':unittest.main()
