"""Explicit-root research ledger. Import never discovers or observes a host."""
import contextlib
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from .safety import safe_path, safe_read_path

MAX_PAGES = 2048

RETENTION = 90 * 86400

KINDS = {'initial', 'correction', 'clarification', 'goal_change', 'accept_plan',
         'accept_result', 'reopen', 'abandon', 'assessment', 'quality', 'observation', 'handoff', 'self_correction'}

LAYERS = {'unknown', 'agents', 'claude', 'rules', 'skill', 'mcp', 'memory', 'tool', 'task', 'harness'}

HOSTS = ('codex', 'claude', 'hermes')

SECRET = re.compile(r'(?i)(?:api[_ -]?key|password|authorization|access[_ -]?token)\s*[:=]|sk-[a-zA-Z0-9_-]{16,}|-----BEGIN .*PRIVATE KEY')

class InputError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def hashed(*values):
    return hashlib.sha256(packed(values).encode()).hexdigest()[:32]

def short(value, limit=512):
    if not isinstance(value, str) or len(value.encode()) > limit or SECRET.search(value):
        raise ValueError('Invalid, oversized or credential-like field')
    return value

def identity(data):
    host = data.get('host', 'codex')
    if host not in HOSTS:
        raise InputError('unknown_host')
    session = data.get('session')
    if not session:
        raise InputError('session_env_missing')
    return host, hashed(host, short(session, 256))

def project(data):
    # Validate before touching storage. No listing/reading the project itself.
    if not data.get('cwd'): raise InputError('cwd_missing')
    return hashed(str(safe_read_path(data['cwd'])))

def setup(root):
    root = safe_path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name in ('hcd.sqlite', 'hcd.sqlite-journal', 'hcd.sqlite-wal', 'hcd.sqlite-shm',
                 'collector-0.lock', 'collector-1.lock', 'review.lock', 'gap', 'latest.json', 'latest.tmp'):
        p = safe_path(root/name, follow_final=False)
        if p.is_symlink():
            raise ValueError('HCD storage must not contain symlinks')
    if (root/'hcd.sqlite-wal').exists():
        raise ValueError('Unexpected WAL; bounded recorder uses DELETE journalling')
    return root

def gap(root):
    try:
        root = setup(root)
        with (root/'gap').open('wb') as f:
            os.chmod(root/'gap', 0o600)
            f.write(b'collection_incomplete\n')
    except (OSError, ValueError):
        pass

@contextlib.contextmanager
def database(root, *, review=False):
    root = setup(root)
    held = None
    for name in (['review.lock'] if review else ['collector-0.lock', 'collector-1.lock']):
        handle = (root/name).open('a'); os.chmod(root/name, 0o600)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held = handle; break
        except BlockingIOError:
            handle.close()
    if held is None:
        raise BlockingIOError('HCD admission full')
    connection = None
    try:
        path = root/'hcd.sqlite'
        if path.exists() and path.stat().st_size > MAX_PAGES * 4096:
            raise ValueError('HCD database exceeds its fixed capacity')
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600); os.close(fd)
        connection = sqlite3.connect(path, timeout=.025)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA page_size=4096')
        if connection.execute('PRAGMA page_size').fetchone()[0] != 4096:
            raise ValueError('Unexpected database page size')
        connection.execute('PRAGMA journal_mode=DELETE')
        connection.execute(f'PRAGMA max_page_count={MAX_PAGES}')
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA secure_delete=ON')
        connection.executescript('''
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, host TEXT, session TEXT, owner TEXT, epoch INTEGER,
          project TEXT, created REAL, touched REAL, initial_id TEXT);
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY, task TEXT REFERENCES tasks(id) ON DELETE CASCADE,
          received REAL, kind TEXT, turn TEXT, payload TEXT, digest TEXT);
        CREATE INDEX IF NOT EXISTS events_task ON events(task,received);
        CREATE TABLE IF NOT EXISTS observations (
          id TEXT PRIMARY KEY, host TEXT, session TEXT, project TEXT, event TEXT, received REAL);
        CREATE TABLE IF NOT EXISTS tool_events (
          id TEXT PRIMARY KEY, host TEXT, session TEXT, call_id TEXT, tool TEXT,
          phase TEXT, status TEXT, received REAL);
        ''')
        yield connection
    finally:
        if connection:
            connection.close()
        held.close()

def record(data, root):
    if not isinstance(data, dict): raise InputError('invalid_request')
    if len(packed(data).encode()) > 8192: raise InputError('oversize')
    project_key = project(data)
    host, session = identity(data)
    if data.get('agent', 'main') != 'main':
        return {'status': 'unattributed', 'reason': 'Only the conversation main agent records task state'}
    kind = data.get('kind')
    if kind not in KINDS: raise ValueError('Unknown event kind')
    task_key = short(data.get('task', ''), 128)
    if not task_key: raise ValueError('Stable task key required')
    task_id = short(data.get('task_id') or hashed(host, session, task_key), 64)
    owner = hashed(host, session, 'main')
    epoch = data.get('epoch', 0)
    if not isinstance(epoch, int) or isinstance(epoch, bool): raise ValueError('Invalid epoch')
    request = short(data.get('request_id', ''), 128)
    if not request: raise ValueError('Idempotency request_id required')
    event_id = hashed(host, session, task_id, request)
    turn = hashed(host, session, short(data['turn'], 128)) if data.get('turn') else None
    payload = {'source': 'agent_reported', 'summary': short(data.get('summary', '')),
               'evidence': short(data.get('evidence', '')), 'layer': data.get('layer', 'unknown'),
               'available_revision': short(data.get('available_revision', 'unknown'), 80),
               'loaded_revision': short(data.get('loaded_revision', 'unknown'), 80)}
    for field in ('target_model', 'skill_name', 'migration_mode'):
        payload[field] = short(data.get(field, 'unknown'), 80)
    for field in ('situation','observed_error'):
        if data.get(field): payload[field]=short(data[field])
    if data.get('internal_task') is True:
        payload['internal_task'] = True
    if payload['layer'] not in LAYERS: raise ValueError('Unknown attribution layer')
    if kind in ('initial', 'correction', 'accept_plan', 'accept_result') and not payload['summary']:
        raise ValueError('Summary required')
    if kind.startswith('accept_') and not payload['evidence']:
        raise ValueError('Acceptance needs natural user evidence; Stop is not acceptance')
    if kind == 'correction': payload['repeated'] = data.get('repeated') is True
    if kind == 'self_correction':
        if not payload['summary'] or not payload['evidence']: raise ValueError('Self correction needs external evidence summary')
        payload['attempt'] = short(data.get('attempt', ''), 128)
        payload['outcome'] = data.get('outcome', 'unknown')
        if payload['outcome'] not in ('recovered', 'failed', 'unknown'): raise ValueError('Invalid recovery outcome')
    if kind == 'assessment':
        distance = data.get('distance'); scope = data.get('scope')
        if type(distance) is not int or distance not in range(5) or scope not in ('plan', 'result'):
            raise ValueError('Assessment requires ordinal distance 0..4 and plan/result scope')
        if not payload['evidence']: raise ValueError('Assessment basis required')
        payload.update(distance=distance, scope=scope)
    if kind == 'quality':
        if data.get('quality') not in ('pass', 'fail', 'unknown'): raise ValueError('Invalid quality')
        payload['quality'] = data['quality']
    if kind == 'handoff':
        target_host, target_session = identity({'host': data.get('to_host'), 'session': data.get('to_session')})
        payload.update(to_host=target_host, to_session=target_session)
    fingerprint = hashed(kind, turn, payload, epoch)
    with database(root) as db:
        with db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT digest FROM events WHERE id=?', (event_id,)).fetchone()
            if prior:
                if prior['digest'] != fingerprint: raise ValueError('Idempotency key reused with different data')
                return {'status': 'duplicate', 'task_id': task_id}
            row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            now = time.time()
            if row is None:
                if data.get('task_id') or epoch: raise ValueError('Unknown continuation task')
                db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)',
                           (task_id, host, session, owner, 0, project_key, now, now, None))
                row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            if row['owner'] != owner or row['epoch'] != epoch:
                raise ValueError('Owner/epoch conflict; explicit handoff required')
            if kind == 'initial' and (row['initial_id'] or db.execute('SELECT 1 FROM events WHERE task=? LIMIT 1', (task_id,)).fetchone()):
                raise ValueError('Cannot replace or backfill the first anchor')
            if kind == 'assessment':
                current = task_summary(db, row)
                if current['initial'] is None or not current['accepted'][payload['scope']]:
                    raise ValueError('No current accepted endpoint or original evidence')
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)',
                       (event_id, task_id, now, kind, turn, packed(payload), fingerprint))
            db.execute('UPDATE tasks SET touched=? WHERE id=?', (now, task_id))
            if kind == 'initial': db.execute('UPDATE tasks SET initial_id=? WHERE id=?', (event_id, task_id))
            if kind == 'handoff':
                db.execute('UPDATE tasks SET host=?,session=?,owner=?,epoch=epoch+1 WHERE id=?',
                           (target_host, target_session, hashed(target_host, target_session, 'main'), task_id))
            return {'status': 'recorded', 'task_id': task_id, 'epoch': epoch + (kind == 'handoff')}

def task_summary(db, row):
    events = list(db.execute('SELECT * FROM events WHERE task=? AND received>=? ORDER BY received,rowid',
                            (row['id'], time.time() - RETENTION)))
    initial = next((e for e in events if e['id'] == row['initial_id']), None)
    state = 'unknown'; distances = {'plan': None, 'result': None}; quality = 'unknown'
    accepted = {'plan': False, 'result': False}
    correction_turns = set(); repeated_turns = set(); unattributed = 0
    counts = {k: 0 for k in ('clarification', 'goal_change', 'correction')}
    for event in events:
        kind = event['kind']; payload = json.loads(event['payload'])
        if kind in counts: counts[kind] += 1
        if kind == 'correction':
            if event['turn']:
                correction_turns.add(event['turn'])
                if payload.get('repeated'): repeated_turns.add(event['turn'])
            else: unattributed += 1
        if kind in ('accept_plan', 'accept_result'):
            state = kind
            scope = kind.removeprefix('accept_')
            accepted[scope] = True
            distances[scope] = None  # A new endpoint needs a new comparison.
        if kind in ('correction', 'self_correction', 'reopen', 'abandon', 'goal_change'):
            state = kind
            accepted = {'plan': False, 'result': False}
            distances = {'plan': None, 'result': None}
            quality = 'unknown'
        if kind == 'assessment' and initial and accepted[payload['scope']]:
            distances[payload['scope']] = payload['distance']
        if kind == 'quality': quality = payload['quality']
    return {'id': row['id'], 'host': row['host'], 'epoch': row['epoch'], 'acceptance': state, 'accepted': accepted,
            'initial': json.loads(initial['payload'])['summary'] if initial else None,
            'anchor': 'agent_reported' if initial else 'missing_or_expired',
            'D_estimate': distances, 'R_observed': len(correction_turns), 'P_observed': len(repeated_turns),
            'unattributed_corrections': unattributed, 'Q': quality, **counts}

def context(data, root):
    root = safe_path(root)
    project(data); host, session = identity(data)
    if not safe_path(root/'hcd.sqlite').exists(): return {'tasks': []}
    with database(root) as db:
        rows = db.execute('SELECT * FROM tasks WHERE host=? AND session=? ORDER BY touched DESC LIMIT 3', (host, session))
        tasks = [task_summary(db, row) for row in rows]
    while len(packed({'tasks': tasks}).encode()) > 2048: tasks.pop()
    return {'tasks': tasks}

def _tick(root, *, student=None):
    root = setup(root)
    with database(root) as db:
        with db:
            cutoff = time.time() - RETENTION
            db.execute('DELETE FROM observations WHERE received<?', (cutoff,))
            db.execute('DELETE FROM events WHERE received<?', (cutoff,))
            db.execute('DELETE FROM tool_events WHERE received<?', (cutoff,))
            db.execute('DELETE FROM tasks WHERE touched<?', (cutoff,))
        now = time.time()
        rows = list(db.execute('SELECT * FROM tasks'))
        tasks = [task_summary(db, r) for r in rows]
        # Weak acceptance: the user moved on for a day without reopening or abandoning.
        settled = [t for r, t in zip(rows, tasks) if r['touched'] < now-86400 and t['acceptance'] not in ('abandon', 'reopen')]
        anchored = [t for t in settled if t['initial'] is not None]
        first_pass = sum(not t['correction'] for t in anchored)
        weekly = [db.execute("SELECT count(*) FROM events WHERE kind='correction' AND received>? AND received<=?",
                             (now-7*86400*(n+1), now-7*86400*n)).fetchone()[0] for n in (0, 1)]
        try:
            from . import patterns
            pattern_report = patterns.summary(root, db, student=student, now=now)
        except (OSError, ValueError, KeyError, sqlite3.Error, json.JSONDecodeError):
            pattern_report = {'status': 'unknown'}
        hooks = {r['host']: {'events': r['n'], 'sessions': r['sessions'], 'last_seen': r['last_seen']} for r in
                 db.execute('SELECT host,count(*) n,count(DISTINCT session) sessions,max(received) last_seen FROM observations GROUP BY host')}
        hook_events = {host: {r['event']: r['n'] for r in db.execute(
            'SELECT event,count(*) n FROM observations WHERE host=? GROUP BY event', (host,))} for host in hooks}
        semantic = db.execute('SELECT count(*) n,coalesce(sum(length(CAST(payload AS BLOB))),0) bytes FROM events').fetchone()
        tool_stats = {r['status']: r['n'] for r in db.execute("SELECT status,count(*) n FROM tool_events WHERE phase<>'PreToolUse' GROUP BY status")}
        tool_stats['distinct_tools'] = db.execute('SELECT count(DISTINCT tool) FROM tool_events').fetchone()[0]
        autonomous = {r['outcome']: r['n'] for r in db.execute("SELECT json_extract(payload,'$.outcome') outcome,count(*) n FROM events WHERE kind='self_correction' GROUP BY outcome")}
        layers = {r['layer']: r['n'] for r in db.execute("SELECT json_extract(payload,'$.layer') layer,count(*) n FROM events WHERE kind='correction' GROUP BY layer")}
    result = {'schema': 3, 'at': now, 'scope': 'explicitly registered tasks in a caller-supplied research ledger',
              'main_signal': 'cross-task correction pattern recurrence; D is secondary',
              'correction_patterns': pattern_report,
              'first_pass': {'settled_with_anchor': len(anchored), 'no_correction': first_pass,
                             'rate': round(first_pass/len(anchored), 3) if anchored else None},
              'acceptance_weak': len(settled),
              'corrections_7d': {'current': weekly[0], 'previous': weekly[1]},
              'registered_tasks': len(tasks), 'actual_task_coverage': 'unknown', 'hook_observations': hooks,
              'acceptance_unknown': sum(not t['accepted']['result'] for t in tasks),
              'acceptance_unknown_by_scope': {s: sum(not t['accepted'][s] for t in tasks) for s in ('plan', 'result')},
              'task_states': {s: sum(t['acceptance'] == s for t in tasks) for s in
                              ('unknown', 'correction', 'self_correction', 'accept_plan', 'accept_result', 'reopen', 'goal_change', 'abandon')},
              'missing_anchors': sum(t['initial'] is None for t in tasks),
              'D_estimate_distribution': {scope: {str(n): sum(t['D_estimate'][scope] == n for t in tasks) for n in range(5)} for scope in ('plan', 'result')},
              'R_observed': sum(t['R_observed'] for t in tasks), 'P_observed': sum(t['P_observed'] for t in tasks),
              'unattributed_corrections': sum(t['unattributed_corrections'] for t in tasks),
              'hook_events': hook_events,
              'recording_cost': {'semantic_events': semantic['n'], 'stored_payload_bytes': semantic['bytes'],
                                 'model_tokens': 'unknown', 'user_time': 'unknown'},
              'quality_failures': sum(t['Q'] == 'fail' for t in tasks), 'correction_layers': layers,
              'tool_outcomes': tool_stats, 'self_corrections_agent_reported': autonomous,
              'source': 'semantic labels are agent_reported, not independently verified user truth',
              'collection_gap': (root/'gap').exists(), 'retention_days': 90}
    host_breakdown = {}
    for host in HOSTS:
        subset = [t for t in tasks if t['host'] == host]
        host_breakdown[host] = {
            'registered_tasks': len(subset),
            'acceptance_unknown': sum(not t['accepted']['result'] for t in subset),
            'missing_anchors': sum(t['initial'] is None for t in subset),
            'R_observed': sum(t['R_observed'] for t in subset),
            'P_observed': sum(t['P_observed'] for t in subset),
            'self_corrections': sum(t.get('self_correction', 0) for t in subset),
        }
    result['host_breakdown'] = host_breakdown
    encoded = packed(result).encode()
    if len(encoded) > 4096: raise ValueError('Report budget exceeded')
    with (root/'latest.tmp').open('wb') as f:
        os.chmod(root/'latest.tmp', 0o600); f.write(encoded)
    os.replace(root/'latest.tmp', root/'latest.json')
    return result


def report(root, *, student=None):
    """Prune expired evidence and report; no model, scheduling, or host inspection."""
    return _tick(root, student=student)
