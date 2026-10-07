"""Synthetic contract tests; no host callbacks, models, or production inputs."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import tomllib
import unittest
from unittest.mock import patch


class ExportTests(unittest.TestCase):
    def test_public_core_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('astra_harness'),
                             'The independently exported research core must exist')

    def test_version_matches_public_package(self):
        from astra_harness import __version__
        root = Path(__file__).resolve().parents[1]
        version = tomllib.loads((root / 'pyproject.toml').read_text())['project']['version']
        self.assertEqual(__version__, version)

    def test_shipped_example_profile_is_disabled(self):
        from astra_harness.profile import validate_profile
        root = Path(__file__).resolve().parents[1]
        profile = tomllib.loads((root / 'examples/research-profile.toml').read_text())
        self.assertEqual(validate_profile(profile), profile)


class CoreTests(unittest.TestCase):
    def setUp(self):
        if importlib.util.find_spec('astra_harness') is None:
            self.skipTest('Run the export existence gate first')
        from astra_harness import hcd, patterns
        self.hcd, self.patterns = hcd, patterns
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'synthetic-ledger'

    def event(self, task='TaskA', kind='initial', request='synthetic-initial-A', **extra):
        data = dict(host='codex', session='synthetic-session-' + task,
                    cwd=str(self.base), task=task, kind=kind, request_id=request,
                    summary='Synthetic direction for ' + task)
        data.update(extra)
        return self.hcd.record(data, self.root)

    def cluster(self):
        def synthetic_runner(packet, schema):
            return {'patterns': [{'key': 'synthetic-check-result',
                'label': 'Synthetic verification omission',
                'description': 'Synthetic tasks omitted an output check.',
                'entry_hint': 'tool',
                'proposed_rule': 'Check the generated output before reporting completion.',
                'event_ids': [c['id'] for c in packet['corrections']]}]}
        return self.patterns.cluster(self.root, synthetic_runner)

    def corrections(self):
        for task in ('TaskA', 'TaskB'):
            self.event(task)
            self.event(task, 'correction', 'synthetic-correction-' + task,
                       summary='Synthetic output check omitted',
                       evidence='Synthetic reviewer requests an output check', turn='synthetic-turn-A')

    def test_identity_must_be_supplied_even_when_host_environment_exists(self):
        with patch.dict(os.environ, {'CODEX_THREAD_ID': 'synthetic-ambient-session'}):
            with self.assertRaises(self.hcd.InputError):
                self.hcd.record(dict(cwd=str(self.base), task='TaskA', kind='initial',
                    request_id='synthetic-request-A', summary='Synthetic initial'), self.root)
        self.assertFalse(self.root.exists())

    def test_data_root_is_required_and_import_creates_no_state(self):
        with self.assertRaises(TypeError):
            self.hcd.record({'kind': 'initial'})
        self.assertFalse(self.root.exists())

    def test_idempotency_rejects_changed_retry(self):
        first = self.event()
        self.assertEqual(self.event()['status'], 'duplicate')
        with self.assertRaises(ValueError):
            self.event(summary='Synthetic changed retry')
        self.assertEqual(first['status'], 'recorded')

    def test_first_anchor_cannot_be_backfilled(self):
        self.event(kind='correction', request='synthetic-correction-A')
        with self.assertRaises(ValueError):
            self.event()

    def test_plan_acceptance_is_not_result_acceptance(self):
        self.event()
        self.event(kind='accept_plan', request='synthetic-plan-A', evidence='Synthetic plan accepted')
        report = self.hcd.report(self.root)
        self.assertEqual(report['acceptance_unknown'], 1)
        self.assertEqual(report['acceptance_unknown_by_scope']['plan'], 0)

    def test_acceptance_requires_evidence_and_stop_is_not_an_event_kind(self):
        self.event()
        with self.assertRaises(ValueError):
            self.event(kind='accept_result', request='synthetic-result-A')
        with self.assertRaises(ValueError):
            self.event(kind='Stop', request='synthetic-stop-A')

    def test_later_correction_invalidates_acceptance_distance_and_quality(self):
        self.event()
        self.event(kind='accept_result', request='synthetic-accept-A', evidence='Synthetic result accepted')
        self.event(kind='assessment', request='synthetic-assess-A', scope='result', distance=0,
                   evidence='Synthetic comparison only')
        self.event(kind='quality', request='synthetic-quality-A', quality='pass')
        self.event(kind='correction', request='synthetic-correction-A', turn='synthetic-turn-A')
        with self.hcd.database(self.root) as db:
            row = db.execute('SELECT * FROM tasks').fetchone()
            result = self.hcd.task_summary(db, row)
        self.assertFalse(result['accepted']['result'])
        self.assertIsNone(result['D_estimate']['result'])
        self.assertEqual(result['Q'], 'unknown')

    def test_self_correction_is_not_a_human_correction(self):
        self.event()
        self.event(kind='self_correction', request='synthetic-self-A',
                   evidence='Synthetic tool failure', outcome='recovered')
        report = self.hcd.report(self.root)
        self.assertEqual(report['R_observed'], 0)
        self.assertEqual(report['self_corrections_agent_reported']['recovered'], 1)
        self.assertEqual(report['host_breakdown']['codex']['self_corrections'], 1)

    def test_expired_evidence_cannot_support_current_distance(self):
        with patch.object(self.hcd.time, 'time', return_value=time.time() - self.hcd.RETENTION - 1):
            self.event()
        with self.assertRaises(ValueError):
            self.event(kind='assessment', request='synthetic-assessment-A', distance=0,
                       scope='result', evidence='Synthetic expired comparison')
        self.event(kind='correction', request='synthetic-current-correction-A')
        self.assertEqual(self.hcd.report(self.root)['missing_anchors'], 1)

    def test_schema_three_keeps_coverage_and_benefit_unknown(self):
        self.event()
        report = self.hcd.report(self.root)
        self.assertEqual(report['schema'], 3)
        self.assertEqual(report['actual_task_coverage'], 'unknown')
        self.assertIn('D is secondary', report['main_signal'])
        self.assertIn('not independently verified', report['source'])

    def test_weak_acceptance_is_separate_from_evidenced_acceptance(self):
        with patch.object(self.hcd.time, 'time', return_value=time.time() - 2 * 86400):
            self.event()
        report = self.hcd.report(self.root)
        self.assertEqual(report['acceptance_weak'], 1)
        self.assertEqual(report['acceptance_unknown'], 1)
        self.assertEqual(report['first_pass']['no_correction'], 1)

    def test_secret_like_input_is_rejected_before_state_creation(self):
        with self.assertRaises(ValueError):
            self.event(summary='password=synthetic-value')
        self.assertFalse(self.root.exists())

    def test_credential_path_is_rejected(self):
        from astra_harness.safety import BoundaryError
        with self.assertRaises(BoundaryError):
            self.hcd.record(dict(host='codex', session='synthetic-session-A',
                cwd=str(self.base / '.ssh'), task='TaskA', kind='initial',
                request_id='synthetic-request-A', summary='Synthetic initial'), self.root)
        self.assertFalse(self.root.exists())

    def test_symlink_storage_is_rejected_without_touching_target(self):
        from astra_harness.safety import BoundaryError
        target = self.base / 'synthetic-target'
        target.mkdir()
        self.root.symlink_to(target, target_is_directory=True)
        with self.assertRaises(BoundaryError):
            self.event()
        self.assertEqual(list(target.iterdir()), [])

    def test_read_only_pattern_connection_does_not_create_a_database(self):
        import sqlite3
        self.root.mkdir()
        with self.assertRaises(sqlite3.OperationalError):
            self.patterns.ro(self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cross_task_pattern_recurs_after_manual_adoption(self):
        self.corrections()
        self.cluster()
        self.assertTrue(self.patterns.adopt(self.root, 'synthetic-check-result',
                                          {'release': 'synthetic-experiment-A'}))
        for task in ('TaskA', 'TaskB'):
            self.event(task, 'correction', 'synthetic-recurrence-' + task,
                       evidence='Synthetic recurrence after intervention', turn='synthetic-turn-B')
        self.cluster()
        stats = self.patterns.recurrence(self.root)[0]
        self.assertEqual(stats['tasks'], 2)
        self.assertEqual(stats['after_adoption'], 2)
        self.assertTrue(any(x['code'].startswith('pattern:') for x in self.patterns.findings(self.root)))

    def test_one_task_cannot_produce_a_cross_task_intervention(self):
        self.event()
        for suffix in ('A', 'B'):
            self.event(kind='correction', request='synthetic-correction-' + suffix)
        self.cluster()
        self.assertFalse(any(x['code'].startswith('pattern:') for x in self.patterns.findings(self.root)))

    def test_invented_cluster_members_cannot_form_a_pattern(self):
        self.corrections()
        def unsupported(packet, schema):
            return {'patterns': [{'key': 'synthetic-unsupported', 'label': 'Synthetic',
                'description': 'Synthetic', 'entry_hint': 'tool', 'proposed_rule': 'Synthetic',
                'event_ids': [packet['corrections'][0]['id'], 'synthetic-invented-member']}]}
        self.assertEqual(self.patterns.cluster(self.root, unsupported)['patterns'], 0)

    def test_student_label_agreement_is_not_user_truth(self):
        self.corrections()
        with self.patterns.connection(self.root) as db:
            ids = [row['id'] for row in self.patterns.corrections(db)]
        result = self.patterns.cluster(self.root, lambda packet, schema: {'patterns': []},
                                       student={ids[0]: 'synthetic-check-result'})
        self.assertEqual(result['student_agreement']['agree'], 0)
        self.assertIn('not user truth', result['student_agreement']['basis'])

    def test_duplicate_single_member_cannot_create_supported_pattern(self):
        item = {'key': 'synthetic-duplicate', 'label': 'Synthetic', 'description': 'Synthetic',
                'entry_hint': 'tool', 'proposed_rule': 'Synthetic',
                'event_ids': ['synthetic-member-A', 'synthetic-member-A']}
        self.assertEqual(self.patterns.validate({'patterns': [item]}, {'synthetic-member-A'}), [])

    def test_cluster_contract_rejects_extra_fields_and_non_list_members(self):
        item = {'key': 'synthetic-contract', 'label': 'Synthetic', 'description': 'Synthetic',
                'entry_hint': 'tool', 'proposed_rule': 'Synthetic',
                'event_ids': ['synthetic-member-A', 'synthetic-member-B']}
        for value in ({'patterns': [item], 'extra': 'synthetic'},
                      {'patterns': [dict(item, event_ids='synthetic-member-A')]},
                      {'patterns': [dict(item, event_ids=[False, 'synthetic-member-A'])]},
                      {'patterns': [dict(item, label=123)]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.patterns.validate(value, {'synthetic-member-A', 'synthetic-member-B'})

    def test_profile_rejects_numeric_boolean_substitutes(self):
        from astra_harness.profile import DEFAULT_PROFILE, validate_profile
        for field, value in (('schema', True), ('integrations', 0)):
            changed = json.loads(json.dumps(DEFAULT_PROFILE))
            if field == 'schema':
                changed['schema'] = value
            else:
                changed['integrations']['observation'] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_profile(changed)

    def test_context_accepts_explicit_string_root(self):
        event = self.event()
        result = self.hcd.context({'host': 'codex', 'session': 'synthetic-session-TaskA',
            'task_id': event['task_id'], 'cwd': str(self.base)}, str(self.root))
        self.assertEqual(result['tasks'][0]['anchor'], 'agent_reported')

    def test_demo_reports_only_synthetic_results_and_refuses_nonempty_root(self):
        from astra_harness.__main__ import synthetic_demo
        result = synthetic_demo(self.root)
        self.assertTrue(result['synthetic'])
        self.assertEqual(result['schema'], 3)
        self.assertEqual(result['benefit'], 'unknown')
        self.assertEqual(result['patterns']['synthetic-check-output'][2], 2)
        before = (self.root / 'hcd.sqlite').read_bytes()
        with self.assertRaises(ValueError):
            synthetic_demo(self.root)
        self.assertEqual((self.root / 'hcd.sqlite').read_bytes(), before)

    def test_default_profile_disables_all_private_integrations(self):
        from astra_harness.profile import DEFAULT_PROFILE, validate_profile
        self.assertTrue(all(value is False for value in DEFAULT_PROFILE['integrations'].values()))
        changed = json.loads(json.dumps(DEFAULT_PROFILE))
        changed['integrations']['observation'] = True
        with self.assertRaises(ValueError):
            validate_profile(changed)


if __name__ == '__main__':
    unittest.main()
