# Evolution and version meanings

**0.1.0 is the first public distribution of this research core.** Earlier internal stages did not have public tags or releases of this repository. The table below is a source/document-grounded design lineage, not a reconstructed public release history. It includes no operational record, personal task trace, production receipt, or historical user-data count.

| Milestone | Problem and architectural change | Basis and limit |
|---|---|---|
| 2026-09-15 internal foundation | Separate supporting configuration engineering from business tasks; add conflict-aware publication and distinguish feedback, hypotheses, evidence, and resolution | Internal foundation commits and publisher/feedback implementation; live publication is excluded here |
| HCD event-state refinement, before public extraction | Distinguish plan/result acceptance; preserve the first direction; invalidate stale acceptance and scores after further correction or expiry | Current event ledger and synthetic regressions; intermediate stages were not publicly tagged |
| 2026-09-21 internal learning direction | Explore a small local student using bounded observations and separated training/validation/test groups | Dated internal design contract and learning implementation; no model, training data, or verified user-benefit claim is distributed |
| Pattern-centered refinement, before public extraction | Use shared cross-task correction causes and post-intervention recurrence as the leading signal, with ordinal D secondary | Current `patterns` implementation and schema 3 report; exact first-change date was not established by a public commit |
| 2026-10-01 internal cloud contract | Bind remote structured decisions to finite-lived evidence and constrained source review/validation/publication | Dated contract and implementation lineage; cloud control and authentication runtime are excluded |
| 2026-10-05 internal MCP interface 1.0.3 | Correct JSON Schema reference placement under the request wrapper | Internal interface version constant and dedicated schema regression change; not a public release of this core |
| 2026-10-07 public research core 0.1.0 | Extract a reusable, explicit-root event and pattern protocol with synthetic examples; omit personal runtime and records | The source and tests in this repository; future public changes are tracked by this repository's commits, tags, and changelog |

## What the public extraction changes

The public implementation retains idempotency, owner/epoch and first-anchor semantics, evidence expiry, resource bounds, acceptance distinctions, pattern support validation, recurrence, and uncertainty markers. It replaces personal paths with explicit caller-supplied state roots and generic credential-class protection. It omits ambient host identity, collectors, scheduling, automatic live adaptation, and model clients.

This extraction narrows the executable scope. It does not imply that the entire internal Harness can be installed from this repository or that excluded authentication/deployment boundaries have been weakened. A local `adopt` call marks a research intervention; it cannot publish a rule to a host.

## Three version domains

| Version domain | Meaning |
|---|---|
| Public package and release `0.1.0` | Version of `astra-harness-research`, this bounded distribution |
| Internal package `1.0.0` | Existing internal packaging lineage; not an earlier public version of this distribution |
| Internal MCP interface `1.0.3` | A remote-interface schema revision; the server is not bundled here |

The internal deployment mechanism also identifies installations by date and content fingerprint. Those operational identifiers are not public package versions and are not copied into this history.

## Research claims that remain open

Engineering tests establish defined behavior with synthetic inputs. They do not establish complete collection, independent semantic truth, lower correction burden, superiority over another memory or agent system, or causal effects of adaptations. Student-versus-clustering label agreement is one diagnostic, not user-verified accuracy. Public milestones will continue to distinguish implementation, reproducible tests, and benefits that remain unknown.
