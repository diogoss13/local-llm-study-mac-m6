# Local LLMs on a 16 GB Mac mini

**Best fit for the tested use case: Qwen 3.5 9B (`qwen3.5:9b-q4_K_M`).** It offered the best observed combination of large-context retrieval, structured tool calls, and instruction-following in this study. With a 4-bit KV cache, it completed six retrieval checks using a **262,144-token configured window and approximately 223,000 actual input tokens**, averaging **11 tokens/s** on short answers.

**Suggested starting point:** Qwen 3.5 with a **131,072-token window and q8_0 KV cache**. It passed all six retrievals at approximately **17 tokens/s**, with about **5 minutes** of initial document processing. The 262k/q4 configuration reached a larger window but required approximately **16 minutes across two processing segments**. This is a recommendation for the measured workload, not a universal model-quality ranking.

**Fastest short-response generation:** DeepSeek Coder V2 16B, at approximately **79 tokens/s**. It also made content and retrieval errors, so raw speed did not make it the best choice for this study's large-context use case.

## Test environment

- Mac mini with Apple M6: 12 CPU cores, 12 integrated GPU cores, 16 GB unified memory.
- External E300 SSD, nominally 512 GB, ExFAT, connected over a 10 Gb/s USB link.
- macOS 27.2.1; Ollama 0.40.15; Python 3.9.6.
- Metal for GGUF models; MLX for Gemma.

See [hardware details](docs/HARDWARE.md). Only technical characteristics needed to interpret or reproduce the study are included.

## Short-context benchmark

One model at a time, one excluded warm-up, then six measured responses. Context: 4,096 tokens; temperature: zero; output cap: 256 tokens.

| Model | Mean tokens/s | Min–max |
|---|---:|---:|
| DeepSeek Coder V2 16B | 78.94 | 77.78–81.99 |
| Gemma 4 12B | 37.92 | 24.86–47.02 |
| Qwen 3.5 9B | 25.12 | 23.35–28.02 |
| Qwen Coder 14B | 15.54 | 15.00–17.04 |

All four passed the arithmetic task and four Python-function cases. Gemma and Qwen 3.5 emitted structured tool calls; Qwen Coder returned the requested call as plain text. Only Qwen 3.5 returned bare JSON as requested. DeepSeek hallucinated an object-detection project when summarizing a passage about SSD storage.

## Long-context benchmark

Selected fully completed runs with six correct code-retrieval answers:

| Model / KV cache | Configured window | Actual input tokens¹ | Mean tokens/s² | Initial processing |
|---|---:|---:|---:|---:|
| Qwen 3.5 / default | 65,536 | 55,770 | 20.52 | 108.6 s |
| Qwen 3.5 / q8_0 | 131,072 | 111,529 | 16.96 | 300.0 s |
| Qwen 3.5 / q4_0 | 262,144 | 223,073 | 10.96 | ~964.9 s³ |
| Gemma / MLX | 65,536 | 56,354 | 15.01 | 137.1 s |
| Qwen Coder / q4_0 | 32,768 | 27,513 | 10.97 | 124.6 s |
| DeepSeek Coder / q4_0 | 32,768 | 27,274 | 35.36 | 34.7 s |

¹ Representative first-query count; later queries can differ by one or two tokens. ² Decode rates on short answers, excluding loading and prompt processing. ³ Accumulated across two segments with partial-prefix reuse, not an uninterrupted cold-prefill measurement.

Gemma completed 64k with approximately **5.6 GiB of system swap** and warning-level memory pressure. Its 131k attempt was stopped. DeepSeek's 64k attempt was stopped for memory use and CPU offload. Both made retrieval errors in separate 16k samples. These are the largest fully completed stages reported here, not proven absolute limits for every model.

## Repeat the experiment

Start Ollama with one loaded model allowed. For the suggested Qwen 131k configuration:

```sh
OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_NO_CLOUD=1 \
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 \
ollama serve
```

In another terminal, from this repository:

```sh
python3 scripts/run_context.py \
  --models 'qwen3.5:9b-q4_K_M' --levels 131072 \
  --output-dir outputs/context-q8
```

For 262k, restart the server with `q4_0`, then use `--levels 262144 --timeout 1800`. Cache precision and context size are separate settings; the installed model weights remain unchanged. See [full reproduction instructions](docs/REPRODUCING.md).

## Scope and data

This exploratory study uses one machine and synthetic documents with codes near the beginning, middle, and end. Six correct retrievals do not certify global reasoning, long-form accuracy, or autonomous coding. Inputs occupied approximately 83%–86% of configured windows. Other applications remained open; cache, swap, and thermal state were not controlled.

Documentation is English. Experimental prompts and model responses retain their original Portuguese wording; the long-document filler is English. They are synthetic test material. Identifying machine metadata, activity timestamps, local filesystem paths, personal setup details, and diagnostic logs are excluded. Numeric results and model-response text were preserved.

- [Methods and limitations](docs/METHODOLOGY.md)
- [Per-model findings](docs/RESULTS.md)
- [All recorded result tables](docs/RESULTS_TABLES.md)
- [Data preparation](docs/DATA_PREPARATION.md)

```text
data/raw/       Measurement records with identifying metadata removed
data/derived/   Recorded validation outcomes and English summaries
docs/           Hardware, methods, results, and reproduction guide
environment/    Relevant hardware, model, and storage specifications
scripts/        Configurable runners and offline summary generator
```

No model weights are included. New measurements belong in the ignored `outputs/` directory. To regenerate the English tables without loading a model:

```sh
python3 scripts/summarize.py
```
