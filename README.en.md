<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="✦ Astra Harness — correction patterns, evidence boundaries, research core" width="100%">
</picture>

# Astra Harness · public research core

[中文](README.md) · English

✦EricMingle69 · MIT · public distribution **0.1.0**

Astra is a personal agent system; Harness is its supporting engineering; **HCD (Human Correction Distance)** is the correction-evaluation module. This repository provides a runnable, deliberately bounded research core: explicit task events, evidence-aware acceptance state, and cross-task correction-pattern recurrence. It contains implementation and synthetic examples, with architecture, evolution, and research directions you can reuse.

It does **not** contain actual conversations, logs, memories, feedback, context, task records, operational receipts, training data, or personal configuration. None of those records are part of a release, even when anonymized. Synthetic examples are named TaskA and TaskB and do not represent a real person or task.

## Run a synthetic experiment

Python 3.11 or later on Linux/macOS is sufficient. Runtime code uses the standard library; POSIX file locks are required. Imports perform no host discovery, observation, training, scheduling, or networking.

From a source checkout:

```sh
PYTHONPATH=src python -B -m unittest discover -s tests -v
python -B scripts/publication_check.py check --root .
DEMO_ROOT="$(mktemp -d)"
PYTHONPATH=src python -B -m astra_harness demo --data-root "$DEMO_ROOT"
```

The demo requires an empty scratch directory and writes a **synthetic** ledger there. It registers initial directions and corrections for TaskA/TaskB, uses a deterministic injected runner to identify a common verification omission, marks a synthetic intervention, and shows recurrence after that intervention. The result retains `benefit: unknown` and `coverage: unknown`; no model or production information is used.

For library use, call `hcd.record(event, data_root)` and `hcd.report(data_root)` with your explicitly selected research root. The caller supplies session and project identity. There is no ambient host-session fallback or automatic installation. The included example profile keeps all integrations disabled and cannot enable unbundled private capabilities.

## What is public

| Capability | Public 0.1.0 | Boundary |
|---|---|---|
| HCD event protocol and SQLite ledger | Implemented | Explicit data root; bounded inputs; idempotency; ownership/epoch checks |
| Acceptance and ordinal distance | Implemented | Plan/result separate; evidence required; later corrections and expiry invalidate stale state |
| Pattern clustering and recurrence | Implemented | Caller-injected structured runner; no bundled model client or automatic scheduler |
| Schema 3 report | Implemented | Pattern recurrence is primary; D is secondary; coverage and user truth remain unknown |
| Student-label agreement | Protocol implemented | Optional caller-supplied labels; agreement with model clustering is not user-verified accuracy |
| Synthetic demo and regression suite | Included | Synthetic fixtures only; no network or inference |
| Native host collection, desktop capture, long-term memory service | Excluded | Private integration adapters and configuration are not distributed |
| Local model training, automatic maintenance, transactional live deployment | Excluded | This package cannot install or run these integrations |
| Cloud maintenance and MCP server | Contract lineage documented only | No cloud endpoint, credentials, authentication implementation, or server is included |

Public tests establish specified engineering behavior. They do not establish reduced human correction, complete observation, model superiority, or a causal benefit.

## Read and contribute

- [Architecture and evidence boundaries](docs/architecture.md)
- [Evolution and version meanings](docs/evolution.md)
- [Concrete research roadmap](docs/research-roadmap.md)
- [Changelog](CHANGELOG.md)
- [Contribution and release process](CONTRIBUTING.md)
- [Public publication and maintenance](docs/PUBLICATION.md)
- [Personal authorship notice](PERSONAL-NOTICE.md)

[Engram](https://github.com/Ming-Sir-69/engram) is a separate long-term knowledge project. Astra's HCD module evaluates correction evidence and recurrence; this public core does not bundle an Engram service or a private integration adapter. The two projects have separate responsibilities and public release histories.

This is the first public distribution. Internal package `1.0.0` and MCP interface `1.0.3` are implementation lineage, not earlier public releases of this core. A new public version follows changes to the public implementation and documented research boundaries.
