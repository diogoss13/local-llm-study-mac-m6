# Reproducing the study

## Requirements

- A local Ollama server and the exact installed model tags listed in [HARDWARE.md](HARDWARE.md).
- Python 3.9 or later, using only its standard library.
- macOS for the context runner's `sysctl` memory telemetry. The context runner is not a cross-platform memory monitor.
- No other generation running on the server. Start with no models loaded.

The publication runners are adapted for public reproduction: English operational messages, configurable paths/server address, an explicit timeout, and the post-session monitoring fix. They preserve the original experimental prompts and task identifiers. Their outputs are new measurements, not the published records in `data/raw/`.

## Start the server

Stop an existing Ollama server before starting another on the same port. Use your own model-store path, or omit `OLLAMA_MODELS` to use Ollama's normal model directory:

```sh
export OLLAMA_MODELS='/path/to/models'
OLLAMA_NO_CLOUD=1 OLLAMA_MAX_LOADED_MODELS=1 ollama serve
```

For the 131k Qwen cache configuration, start the server with:

```sh
OLLAMA_MODELS='/path/to/models' \
OLLAMA_NO_CLOUD=1 OLLAMA_MAX_LOADED_MODELS=1 \
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 \
ollama serve
```

Use `q4_0` instead of `q8_0` for the recorded maximum-window configuration. These server-level settings apply separately from the per-request `num_ctx`. Do not assume they configure the MLX backend identically. No model weights or third-party model licenses are included in this repository.

## Run the short benchmark

From the repository root, in another terminal:

```sh
python3 scripts/run_benchmark.py --output-dir outputs/short
```

To select a model or another API port:

```sh
python3 scripts/run_benchmark.py \
  --models 'qwen3.5:9b-q4_K_M' \
  --base-url http://127.0.0.1:11434 \
  --output-dir outputs/qwen-short
```

The short runner emits one warm-up and six measured responses per model, followed by the tool check when advertised. It records the responses; it does not execute generated code. Recorded code-validation results remain in `data/derived/benchmark-validation.json`.

## Run selected context windows

```sh
python3 scripts/run_context.py \
  --models 'qwen3.5:9b-q4_K_M' \
  --levels 16384,32768,65536 \
  --output-dir outputs/context-default
```

With the server restarted using q8_0:

```sh
python3 scripts/run_context.py \
  --models 'qwen3.5:9b-q4_K_M' --levels 131072 \
  --output-dir outputs/context-q8
```

With q4_0 and an extended timeout for the maximum window:

```sh
python3 scripts/run_context.py \
  --models 'qwen3.5:9b-q4_K_M' --levels 262144 \
  --timeout 1800 --output-dir outputs/context-q4
```

Keep new measurements in `outputs/` so archived evidence is not overwritten. The runner checks unloading between stages and stops escalating a model after a failed stage. Model-level context caps come from the study's recorded metadata. The adjusted guard may stop a run earlier than the historical manually supervised attempts. After interruption, confirm the model is unloaded with Ollama before another run.

For a fresh maximum-window run, use the maintained context runner with an extended timeout. The historical 262k timing used a partial-prefix continuation, so a new uninterrupted run is not an identical timing experiment.

## Rebuild English summaries without inference

```sh
python3 scripts/summarize.py
```

This reads the publication's historical JSON, computes means and counts, and writes `data/derived/summary.en.json` and `docs/RESULTS_TABLES.md`. It does not contact Ollama, load a model, or execute generated code. It consumes only the bundled historical file schema; new runner outputs need separate analysis or explicit integration.

## Verify file integrity

The root `SHA256SUMS.txt` covers publication files, excluding itself, generated `outputs/`, Git internals, and macOS auxiliary files. On macOS:

```sh
shasum -a 256 -c SHA256SUMS.txt
```

Regenerate the publication manifest after intentionally changing documentation or derived files. The manifest covers this public, metadata-filtered package.
