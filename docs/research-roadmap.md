# Research roadmap with reproducible examples

The research question is whether an evidence-aware correction protocol can help find recurring failure mechanisms while preserving uncertainty and reducing unnecessary rule growth. This repository supplies the protocol and synthetic experiments. It does not publish actual user records or report real-user effectiveness.

## 1. Evidence-state correctness

Hypothesis: keeping initial direction, plan acceptance, result acceptance, and later correction distinct prevents stale success assessments.

Reproduce the synthetic sequence: TaskA initial → plan accepted → result accepted → D estimate → quality pass → further correction. Assert that result acceptance, D, and quality return to unknown. Then age the initial evidence beyond retention while keeping a current correction; assert that a new distance assessment is rejected. Include reopening, changed goals, and missing anchors as counterexamples. The public regression suite covers these invariants; passing them establishes state-machine behavior, not a user's satisfaction.

Next direction: test additional event-order and ownership counterexamples, including explicit handoff and conflicting retries. New acceptance semantics need an observable counterexample before implementation.

## 2. Shared cause and post-intervention recurrence

Hypothesis: grouping corrections by a shared actionable cause across tasks gives a more useful investigation unit than one scalar score per task.

Use TaskA and TaskB with independently generated synthetic verification omissions. Cluster them with a deterministic structured runner into a synthetic output-check pattern. Mark an intervention without modifying any host. Introduce the same omission again in both tasks and compare `after_adoption`, task count, and provisional count. Add a TaskA-only cluster and an invented member as negative controls; neither should justify a cross-task intervention. The bundled demo and tests implement this experiment.

Next direction: compare alternative clustering strategies on a fully synthetic corpus with known generation labels. Freeze the corpus generator and hold out task families before tuning. Report assignment coverage, supported-member rate, fragmentation, false merges, and runtime cost. Synthetic ground truth can evaluate the generator's labels; it cannot stand in for real-user truth.

## 3. Teacher/student disagreement as a diagnostic

Hypothesis: a small provisional classifier can reduce repeated classification cost while making disagreement with a more expensive clustering method visible.

Supply synthetic provisional labels for new observations, then run a deterministic clustering assignment that deliberately disagrees. Confirm the agreement denominator and mismatch count, and retain `not user truth` provenance. Avoid treating unlabelled cases as verified successes or selecting a model with its final test split.

Next direction: implement a separate optional adapter only after its resource budget, grouping/holdout protocol, and failure cases are documented. Model training and inference are currently excluded; no weights, adapters, or training records will be added to public releases.

## 4. Intervention evaluation without self-reward

Hypothesis: recurrence and effort measures can reveal useful candidate interventions, but temporal improvement alone cannot establish causation.

For a synthetic comparison, create two task families with a fixed failure generator and predeclare an intervention that changes only one mechanism. Keep an untouched control family, preserve the event denominator, and report changes in recurrence, unknown acceptance, task difficulty, and resource cost. A decreasing count with a decreasing number of tasks is not automatically an improvement.

Next direction: define a prospective private evaluation protocol before observing real outcomes. Any public account of that research must be a freshly written methodology or conclusion with a clear evidence boundary; actual records, excerpts, identifiers, aggregates presented as operational receipts, and anonymized raw rows remain excluded by this repository's release policy.

## 5. Sustainable public maintenance

Every public update should identify a problem, a concrete change, a falsifiable synthetic test, and an uncertainty boundary. Update architecture, evolution, and changelog when the public interface or research interpretation changes. CI runs the full synthetic suite and public-tree boundary check; maintainers review the exact payload before merging and tagging a version.

A new public module must have a clear reusable purpose and a safe dependency closure. Personal integration adapters are not automatically exported when the private system evolves. Release sources and synthetic examples are the research artifact; collecting or publishing user records is outside this project.
