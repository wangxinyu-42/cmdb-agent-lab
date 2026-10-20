"""Offline scripted planner and an optional chat-completions tool-call adapter."""
import json
import os
import re
import uuid
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .tools import tool_specs

def call(name, args):
    return {'id': 'call_' + uuid.uuid4().hex[:12], 'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)}}

def is_write_request(question):
    return bool(re.search(r'删除|修改|更新|重启|清空|写入|执行命令|\b(delete|drop|update|reboot|shutdown|exec)\b',
                          question, re.I))

class DemoProvider:
    """Deterministic patterns, not an LLM. Deliberately limited grammar."""
    name = 'demo'

    def complete(self, messages, timeout=30):
        if messages[-1]['role'] == 'tool':
            return {'role': 'assistant', 'content': '工具查询完成。'}
        q = messages[1]['content'].strip()
        if is_write_request(q):
            return {'role': 'assistant', 'content': '当前项目只支持只读查询，不能执行资产变更。'}
        racks = list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])[A-Z]\d{2}(?![A-Za-z0-9])', q.upper())))
        ids = list(dict.fromkeys(re.findall(r'(?<![A-Z0-9])SYN-\d{3}(?![A-Z0-9])', q.upper())))
        envs = [e for e in ('test', 'dev', 'prod') if re.search(r'\b' + e + r'\b', q, re.I)]
        if '测试环境' in q and 'test' not in envs:
            envs.append('test')
        if '开发环境' in q and 'dev' not in envs:
            envs.append('dev')
        if '生产环境' in q and 'prod' not in envs:
            envs.append('prod')
        if len(racks) > 1 or len(ids) > 1 or len(envs) > 1:
            return {'role': 'assistant', 'content': '请一次指定一个机柜、一个环境或一台设备，再分别比较。'}
        audit = bool(re.search(r'稽核|异常|检查|audit', q, re.I))
        query = bool(re.search(r'查询|查看|设备|资产|详情|list|asset|detail', q, re.I))
        if not (audit or query):
            return {'role': 'assistant', 'content': '支持资产查询、单设备详情和数据稽核。请明确机柜或设备 ID。'}
        # Unsupported constraints must not silently turn into an unfiltered query.
        rack_tokens = re.findall(r'(?<![A-Z0-9])[A-Z]\d+(?![A-Z0-9])', q.upper())
        env_tokens = re.findall(r'\b(?:in|environment|env)\s+([a-z][a-z0-9_-]*)\b', q, re.I)
        if (any(t not in racks for t in rack_tokens)
                or any(t.lower() not in envs and t.upper() not in racks for t in env_tokens)
                or ('SYN-' in q.upper() and not ids)
                or re.search(r'\b(?:qa|staging|uat|production|development|testing)\b', q, re.I)):
            return {'role': 'assistant', 'content': '请补充有效筛选条件：机柜如 A01，设备如 SYN-003，环境仅支持 test / dev / prod。'}
        if re.search(r'排除|除了|不在|非测试|非开发|非生产|\b(?:not|except|excluding)\b', q, re.I):
            return {'role': 'assistant', 'content': '暂不支持排除条件，请使用单个机柜、环境或设备 ID 的精确查询。'}
        if ('机柜' in q and not racks) or ('环境' in q and not envs):
            return {'role': 'assistant', 'content': '请补充机柜编号（如 A01）或环境（test / dev / prod）。'}
        args = {}
        if racks:
            args['rack'] = racks[0]
        if envs:
            args['environment'] = envs[0]
        if ids and args:
            return {'role': 'assistant', 'content': '设备 ID 查询暂不混用机柜或环境过滤，请拆分问题。'}
        calls = []
        if query or (audit and not ids):
            calls.append(call('get_asset', {'asset_id': ids[0]}) if ids else call('list_assets', args))
        if audit:
            calls.append(call('audit_assets', {'asset_id': ids[0]} if ids else args))
        return {'role': 'assistant', 'content': None, 'tool_calls': calls}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward Authorization to an unexpected origin.

class LlamaProvider:
    name = 'llama'

    def __init__(self):
        self.base = os.environ.get('LLAMA_BASE_URL', '').rstrip('/')
        self.model = os.environ.get('LLAMA_MODEL', '')
        p = urlparse(self.base)
        if (p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password
                or p.query or p.fragment or not self.model or len(self.model) > 200):
            raise ValueError('Configure LLAMA_BASE_URL and LLAMA_MODEL')
        if p.scheme == 'http' and p.hostname not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('Remote model endpoint requires HTTPS')

    def complete(self, messages, timeout=30):
        body = {'model': self.model, 'messages': messages, 'tools': tool_specs(),
                'tool_choice': 'auto', 'temperature': 0, 'max_tokens': 800, 'stream': False}
        headers = {'Content-Type': 'application/json'}
        key = os.environ.get('LLAMA_API_KEY')
        if key:
            headers['Authorization'] = 'Bearer ' + key
        request = Request(self.base + '/chat/completions', data=json.dumps(body).encode(),
                          headers=headers, method='POST')
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('response_limit')
        return json.loads(raw)['choices'][0]['message']

def model_configured():
    try:
        LlamaProvider()
        return True
    except ValueError:
        return False
