import hashlib
import json
import unittest
from cmdb_agent.tools import DATA, execute_tool
from cmdb_agent.providers import call, LlamaProvider
from cmdb_agent.runtime import run
from cmdb_agent.evaluation import evaluate
from unittest.mock import patch

class Scripted:
    name = 'scripted'
    def __init__(self, messages):
        self.messages = iter(messages)
    def complete(self, messages, timeout=30):
        return next(self.messages)

def message(*calls):
    return {'role': 'assistant', 'content': None, 'tool_calls': list(calls)}

class RuntimeTests(unittest.TestCase):
    def test_fixed_regression_cases(self):
        report = evaluate()
        self.assertEqual(report['passed'], report['total'], [c for c in report['cases'] if not c['passed']])

    def test_trace_sequence_and_readonly(self):
        before = hashlib.sha256(DATA.read_bytes()).hexdigest()
        events = list(run('查询 A01 机柜的设备，并检查数据异常'))
        self.assertEqual([e['event'] for e in events], ['start','tool','tool','final'])
        self.assertEqual([e['sequence'] for e in events], [1,2,3,4])
        self.assertEqual(len({e['trace_id'] for e in events}), 1)
        self.assertEqual(events[-1]['tool_calls'], 2)
        self.assertTrue(events[-1]['grounded'])
        self.assertEqual(hashlib.sha256(DATA.read_bytes()).hexdigest(), before)

    def test_tool_schema_boundary(self):
        bad = [('delete_assets', {}, 'unknown_tool'), ('list_assets', [], 'invalid_arguments'),
               ('list_assets', {'shell':'rm'}, 'invalid_arguments'), ('get_asset', {}, 'missing_argument'),
               ('list_assets', {'rack':1}, 'invalid_argument_value'),
               ('list_assets', {'rack':''}, 'invalid_argument_value'),
               ('list_assets', {'rack':'x'*65}, 'invalid_argument_value')]
        for name, args, code in bad:
            with self.subTest(code=code, args=args):
                self.assertEqual(execute_tool(name,args)['error'], code)

    def test_multiround_model_path(self):
        p = Scripted([message(call('get_asset', {'asset_id':'SYN-003'})),
                      message(call('audit_assets', {'asset_id':'SYN-003'})),
                      {'role':'assistant','content':'SYN-003 的 IP 不合法。'}])
        events = list(run('查询并稽核 SYN-003', p))
        self.assertEqual(events[-1]['event'], 'final')
        self.assertEqual(events[-1]['assets'][0]['id'], 'SYN-003')
        self.assertEqual(events[-1]['issues'][0]['code'], 'invalid_ipv4')
        self.assertFalse(events[-1]['grounded'])

    def test_unknown_write_tool_never_runs(self):
        p = Scripted([message(call('delete_assets', {})), {'role':'assistant','content':'无法执行。'}])
        events = list(run('列出设备', p))
        self.assertEqual(events[1]['result'], {'error':'unknown_tool'})
        self.assertEqual(events[-1]['assets'], [])

    def test_malformed_json_feedback(self):
        c = call('list_assets', {})
        c['function']['arguments'] = '{'
        events = list(run('查询设备', Scripted([message(c),{'role':'assistant','content':'参数错误。'}])))
        self.assertEqual(events[1]['result']['error'], 'malformed_json')

    def test_budget_limits(self):
        self.assertEqual(list(run('查询设备', Scripted([message(call('list_assets', {}))]),max_rounds=1))[-1]['code'], 'round_budget_exceeded')
        p=Scripted([message(call('list_assets', {}),call('audit_assets', {}))])
        self.assertEqual(list(run('查询设备',p,max_calls=1))[-1]['code'],'tool_budget_exceeded')

    def test_duplicate_and_invalid_calls(self):
        c=call('list_assets',{})
        self.assertEqual(list(run('查询设备',Scripted([message(c,c)])))[-1]['code'],'duplicate_call_id')
        self.assertEqual(list(run('查询设备',Scripted([message({'id':3})])))[-1]['code'],'invalid_tool_call')

    def test_provider_error_redacted(self):
        class Failing:
            name='failing'
            def complete(self,*args,**kwargs):
                raise ValueError('Authorization: SECRET_NEVER_LOG')
        events=list(run('查询设备',Failing()))
        self.assertEqual(events[-1]['code'],'provider_error')
        self.assertNotIn('SECRET',json.dumps(events))

    def test_blank_input(self):
        for q in ('', ' ', 'x'*2001, None, 10):
            with self.subTest(q=q), self.assertRaises(ValueError):
                list(run(q))

    def test_deadline_and_invalid_answer(self):
        class Slow:
            name='slow'
            def complete(self,*args,**kwargs):
                import time
                time.sleep(.01)
                return {'role':'assistant','content':'done'}
        self.assertEqual(list(run('查询设备',Slow(),deadline=.001))[-1]['code'],'deadline_exceeded')
        self.assertEqual(list(run('查询设备',Scripted([{'role':'assistant','content':None}])))[-1]['code'],'invalid_answer')

    def test_endpoint_config(self):
        for url in ('http://example.com/v1','https://user:secret@example.com/v1',
                    'https://example.com/v1?key=secret','file:///etc/passwd'):
            with self.subTest(url=url), patch.dict('os.environ',{'LLAMA_BASE_URL':url,'LLAMA_MODEL':'test'}), self.assertRaises(ValueError):
                LlamaProvider()

if __name__ == '__main__':
    unittest.main()
