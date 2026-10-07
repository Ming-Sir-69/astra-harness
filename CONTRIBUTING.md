# Contributing and public maintenance

Contributions should improve the reusable correction-research protocol, its evidence boundaries, or a reproducible synthetic experiment. Propose a concrete problem and how a test can falsify the proposed behavior. Use synthetic TaskA/TaskB examples and independently written documentation.

Do not submit actual conversations, prompts, records, feedback, memories, context, logs, screenshots, training data, adapters, weights, operational receipts, personal configuration, credentials, host endpoints, or identifiers. This remains prohibited when data has been anonymized or redacted. Reproduce defects with freshly invented fixtures; do not turn a private row into a public fixture.

## Pull request checks

1. State the problem, final behavior, evidence basis, and known limitation.
2. Add or update a meaningful synthetic regression or reproducible research protocol.
3. Run the full standard-library test suite and the public-tree check.
4. Keep integration profiles disabled. Do not add ambient host discovery, arbitrary execution, or automatic installation.
5. Update README, architecture/evolution, and CHANGELOG when public scope, interfaces, or interpretation changes.
6. Update the declared file allowlist explicitly and review every new path. Reject symlinks and nested repositories.

```sh
PYTHONPATH=src python -B -m unittest discover -s tests -v
python -B scripts/publication_check.py check --root .
```

## Release process

Maintainers review the exact public payload and dependency ownership, not a private working directory. CI checks source/tests/docs against the public allowlist, validates the disabled profile, and runs only synthetic offline tests. Security review and implementation review should agree on the release payload before merge.

Increment `pyproject.toml` and `astra_harness.__version__` together; write the change, reason, replacement/tradeoff, verification, research interpretation, limitation, and next direction in the public changelog/evolution documents. Create a matching public tag and GitHub release from the reviewed source tree. Release attachments must contain only allowlisted source and documentation; never upload operational receipts or audit logs.

Checks are defense in depth. They cannot prove arbitrary prose contains no private fact, so review is still necessary. Ongoing maintenance means reviewed public changes and release gates; it does not mean automatic synchronization or background collection from a personal computer.

## Attribution

Preserve MIT notices for this project's own source and documentation. Runtime dependencies are Python standard-library modules; no third-party library source, model artifact, or dataset is bundled. A future dependency or borrowed implementation requires its license and attribution before inclusion.
