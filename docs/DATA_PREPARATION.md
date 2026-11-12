# Public dataset preparation

The public package retains the numerical measurements, model tags and digests, generated response text, synthetic test fixtures, and relevant technical environment. The source files were filtered for publication.

## Excluded material

- Full machine inventory, device/SKU identifiers, display and peripheral details.
- Personal filesystem and application paths, external-volume labels, and local setup details.
- Exact response/model activity timestamps and location/time-zone metadata.
- Server diagnostic logs, terminal progress logs, early setup attempts, and preparation history.
- Historical scripts and reports tied to the original local folder layout.

A private source copy was kept outside the publication directory. It is not included in this repository. Public checksum values describe the filtered dataset; they do not claim byte identity with the private originals.

## Preserved evidence

Measured token counts, durations, decode rates, pass/fail outcomes, expected codes, configured windows, document hashes, and model-response text were checked against the source records after filtering and remained unchanged. Text in generated answers is synthetic benchmark output, not private user documents.

Prompts and answers were not translated because their language is part of the workload. English documentation and summary labels explain the original Portuguese records. Some error annotations remain in Portuguese and describe resource-related interruptions.

The maintained scripts have configurable output and API settings. Offline checks exercised both runners against a temporary mocked Ollama API, confirmed six measured queries and unloading, compared original prompt fixtures and deterministic document generation, and matched recomputed short-benchmark means to the recorded validation results. The full inference battery was not repeated during publication preparation.

The README's recommendation applies to this study's large-context use case. Faster decode alone, or six successful retrievals, does not establish general model superiority.
