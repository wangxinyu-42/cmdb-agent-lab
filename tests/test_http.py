import http.client
import json
import threading
import unittest
from unittest.mock import patch
from cmdb_agent.server import Server
from cmdb_agent.providers import LlamaProvider

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = Server(('127.0.0.1',0))
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(2)

    def request(self,path='/',method='GET',data=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        c.request(method,path,body=data,headers=headers or {})
        r=c.getresponse();status=r.status;headers=dict(r.getheaders());body=r.read();c.close()
        return status,headers,body

    def test_sse_transport(self):
        status,headers,body=self.request('/api/chat','POST',json.dumps({'question':'查询 A01 机柜的设备，并检查数据异常'}),{'Content-Type':'application/json'})
        self.assertEqual(status,200)
        self.assertIn('text/event-stream',headers['Content-Type'])
        events=[json.loads(line[6:]) for line in body.decode().splitlines() if line.startswith('data: ')]
        self.assertEqual(events[-1]['event'],'final')
        self.assertEqual(len(events[-1]['assets']),3)
        self.assertEqual(len(events[-1]['issues']),2)

    def test_invalid_json_and_origin(self):
        for body in ('{','[]','{"question":""}','{"question":1}'):
            self.assertEqual(self.request('/api/chat','POST',body,{'Content-Type':'application/json'})[0],400)
        self.assertEqual(self.request('/api/chat','POST','{}',{'Content-Type':'application/json','Origin':'https://example.com'})[0],403)
        self.assertEqual(self.request('/api/chat','POST','{}',{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.request('/api/chat','POST','x'*8193,{'Content-Type':'application/json'})[0],400)

    def test_host_and_path_boundary(self):
        self.assertEqual(self.request('/api/health',headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.request('/%2e%2e/cmdb_agent/assets.json')[0],404)
        self.assertEqual(self.request('/api/assets?rack=A01&rack=B02')[0],400)
        self.assertEqual(self.request('/api/assets?owner=demo-team-a')[0],400)

    def test_asset_filter_and_health(self):
        self.assertEqual(json.loads(self.request('/api/assets?rack=B02')[2])['count'],2)
        self.assertEqual(json.loads(self.request('/api/health')[2])['data'],'synthetic')

    def test_real_adapter_against_http_fixture(self):
        # Protocol verification only; this fixture is not a language model.
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        captured=[]
        class Fixture(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                captured.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                raw=json.dumps({'choices':[{'message':{'role':'assistant','content':'fixture response'}}]}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        fixture=ThreadingHTTPServer(('127.0.0.1',0),Fixture)
        t=threading.Thread(target=fixture.serve_forever,daemon=True);t.start()
        try:
            with patch.dict('os.environ',{'LLAMA_BASE_URL':f'http://127.0.0.1:{fixture.server_port}/v1','LLAMA_MODEL':'fixture'}):
                result=LlamaProvider().complete([{'role':'user','content':'查询设备'}])
            self.assertEqual(result['content'],'fixture response')
            self.assertEqual(len(captured[0]['tools']),3)
        finally:
            fixture.shutdown();fixture.server_close();t.join(2)

if __name__ == '__main__':
    unittest.main()
