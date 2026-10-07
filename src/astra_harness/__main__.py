"""An explicit, synthetic demo; never connects to hosts or a model."""
import argparse
import json
from pathlib import Path
from . import hcd, patterns
from .safety import safe_path


def synthetic_demo(root):
    root = safe_path(root)
    if root.exists() and any(root.iterdir()):
        raise ValueError('Synthetic demo requires an empty scratch directory')
    for task in ('TaskA', 'TaskB'):
        base = dict(host='codex', session='synthetic-session-' + task, task=task, cwd=str(root))
        hcd.record(dict(base, kind='initial', request_id='synthetic-initial-' + task,
                        summary='Synthetic initial direction'), root)
        hcd.record(dict(base, kind='correction', request_id='synthetic-correction-' + task,
                        summary='Synthetic output was not checked',
                        evidence='Synthetic reviewer asks for an output check', turn='synthetic-turn-A'), root)
    def synthetic_runner(packet, schema):
        return {'patterns': [{'key': 'synthetic-check-output', 'label': 'Synthetic output check',
            'description': 'Synthetic examples omit verification.', 'entry_hint': 'tool',
            'proposed_rule': 'Check output before reporting completion.',
            'event_ids': [row['id'] for row in packet['corrections']]}]}
    patterns.cluster(root, synthetic_runner)
    patterns.adopt(root, 'synthetic-check-output', {'release': 'synthetic-intervention-A'})
    for task in ('TaskA', 'TaskB'):
        hcd.record(dict(host='codex', session='synthetic-session-' + task, task=task,
            cwd=str(root), kind='correction', request_id='synthetic-recurrence-' + task,
            summary='Synthetic recurrence after intervention', evidence='Synthetic output remains unchecked',
            turn='synthetic-turn-B'), root)
    patterns.cluster(root, synthetic_runner)
    report = hcd.report(root)
    return {'synthetic': True, 'schema': report['schema'],
            'patterns': report['correction_patterns']['top'],
            'acceptance_unknown': report['acceptance_unknown'],
            'coverage': report['actual_task_coverage'], 'benefit': 'unknown'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='Run deterministic synthetic tasks in an empty scratch directory')
    demo.add_argument('--data-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(synthetic_demo(args.data_root), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
