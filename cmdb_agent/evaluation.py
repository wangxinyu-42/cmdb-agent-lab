"""Small, transparent regression set; not a general LLM benchmark."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from .runtime import run
from .tools import DATA

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / 'evals' / 'report.json'

def evaluate(provider=None):
    cases = json.loads((ROOT / 'evals' / 'cases.json').read_text(encoding='utf-8'))
    results = []
    for case in cases:
        events = list(run(case['question'], provider=provider))
        final = events[-1]
        actual_ids = sorted(a['id'] for a in final.get('assets', []))
        actual_issues = sorted(i['asset_id'] + ':' + i['code'] for i in final.get('issues', []))
        actual_tools = [e['name'] for e in events if e['event'] == 'tool']
        checks = {'finished': final['event'] == 'final',
                  'asset_ids': actual_ids == sorted(case['assets']),
                  'issues': actual_issues == sorted(case['issues']),
                  'tools': actual_tools == case['tools']}
        if case.get('answer_contains'):
            checks['answer'] = case['answer_contains'] in final.get('answer', '')
        results.append({'id': case['id'], 'question': case['question'], 'passed': all(checks.values()),
                        'checks': checks, 'actual_assets': actual_ids, 'actual_issues': actual_issues,
                        'actual_tools': actual_tools, 'terminal_event': final['event']})
    return {'generated_at': datetime.now(timezone.utc).isoformat(),
            'provider': provider.name if provider else 'demo', 'python': platform.python_version(),
            'fixture_sha256': hashlib.sha256(DATA.read_bytes()).hexdigest(),
            'passed': sum(r['passed'] for r in results), 'total': len(results),
            'scope': '固定合成数据与确定性路由回归；不代表真实模型准确率或生产性能。', 'cases': results}

def main():
    import argparse
    from .providers import LlamaProvider
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=('demo', 'llama'), default='demo')
    parser.add_argument('--output', type=Path, default=REPORT)
    args = parser.parse_args()
    report = evaluate(LlamaProvider() if args.provider == 'llama' else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"{report['provider']}: {report['passed']}/{report['total']} — {args.output}")
    raise SystemExit(0 if report['passed'] == report['total'] else 1)

if __name__ == '__main__':
    main()
