"""The only data access boundary. No shell, arbitrary URL or write tool."""
import ipaddress
import json
from pathlib import Path

DATA = Path(__file__).with_name('assets.json')
FIELDS = {'list_assets': ('rack', 'environment'), 'get_asset': ('asset_id',),
          'audit_assets': ('rack', 'environment', 'asset_id')}
LABELS = {'missing_owner': '缺少负责人', 'missing_rack': '缺少机柜',
          'invalid_ipv4': 'IPv4 地址不合法', 'duplicate_ipv4': 'IPv4 地址重复'}

def assets():
    return json.loads(DATA.read_text(encoding='utf-8'))

def tool_specs():
    descriptions = {'list_assets': '按精确机柜 rack 或环境 environment 查询合成资产。',
                    'get_asset': '按 asset_id 获取设备详情。',
                    'audit_assets': '检查缺少负责人、缺少机柜、非法或重复 IPv4；重复检查覆盖全量合成台账，结果仅返回筛选资产。'}
    return [{'type': 'function', 'function': {
        'name': name, 'description': descriptions[name],
        'parameters': {'type': 'object', 'properties': {
            field: {'type': 'string', 'maxLength': 64} for field in fields},
            'required': ['asset_id'] if name == 'get_asset' else [],
            'additionalProperties': False}}} for name, fields in FIELDS.items()]

def execute_tool(name, args, *, inventory=None):
    if name not in FIELDS:
        return {'error': 'unknown_tool'}
    if not isinstance(args, dict) or set(args) - set(FIELDS[name]):
        return {'error': 'invalid_arguments'}
    if name == 'get_asset' and 'asset_id' not in args:
        return {'error': 'missing_argument'}
    if any(type(v) is not str or not v.strip() or len(v) > 64 for v in args.values()):
        return {'error': 'invalid_argument_value'}
    inventory = assets() if inventory is None else inventory
    rows = [a for a in inventory if all(a.get('id' if k == 'asset_id' else k) == v
                                     for k, v in args.items())]
    source = {'source': 'synthetic_fixture', 'assets': rows}
    if name == 'get_asset':
        return {**source, 'found': bool(rows), 'asset': rows[0] if rows else None}
    if name == 'list_assets':
        return {**source, 'count': len(rows)}
    issues = []
    # Scan the inventory before filtering: a conflict can live in another rack.
    ip_peers = {}
    for a in inventory:
        try:
            ip = str(ipaddress.IPv4Address(a['ip']))
        except ipaddress.AddressValueError:
            continue
        ip_peers.setdefault(ip, set()).add(a['id'])
    for a in rows:
        codes = []
        if not a['owner'].strip():
            codes.append('missing_owner')
        if not a['rack'].strip():
            codes.append('missing_rack')
        try:
            ipaddress.IPv4Address(a['ip'])
        except ipaddress.AddressValueError:
            codes.append('invalid_ipv4')
        issues.extend({'asset_id': a['id'], 'code': code, 'message': LABELS[code]}
                      for code in codes)
        peers = sorted(ip_peers.get(a['ip'], set()) - {a['id']})
        if peers:
            issues.append({'asset_id': a['id'], 'code': 'duplicate_ipv4',
                           'message': LABELS['duplicate_ipv4'], 'related_asset_ids': peers})
    return {**source, 'asset_count': len(rows), 'issue_count': len(issues), 'issues': issues}
