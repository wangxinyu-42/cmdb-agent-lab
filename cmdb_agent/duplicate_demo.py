"""Reproduce a cross-rack IP conflict in memory without changing assets.json."""
import json
from .tools import assets, execute_tool


def main():
    inventory = assets()
    inventory[4]['ip'] = inventory[0]['ip']
    report = {
        'scope': '合成数据工具级演示；仅在内存制造 SYN-001 与 SYN-005 的跨机柜 IP 冲突，不改写资产文件。',
        'single_asset': execute_tool('audit_assets', {'asset_id': 'SYN-001'}, inventory=inventory),
        'rack_a01': execute_tool('audit_assets', {'rack': 'A01'}, inventory=inventory),
        'all_assets': execute_tool('audit_assets', {}, inventory=inventory),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
