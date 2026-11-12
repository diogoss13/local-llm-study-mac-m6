# Methodology and limitations

## Session design

One machine, one exploratory session, and one loaded model at a time. `OLLAMA_MAX_LOADED_MODELS=1` was used, and `/api/ps` was checked after unloading between stages. Models were tested sequentially, not as competing simultaneous workloads. The final short benchmark was run after the SSD cable change.

There was no randomized run order, isolated operating-system workload, controlled thermal state, statistical replication across independent sessions, or clearing of all disk/prefix caches. Results should not be interpreted as population-level estimates or a controlled comparison of model architectures.

## Short-context benchmark

Each model received a warm-up request followed by six measured tasks. Settings: 4,096-token context, temperature 0, 256-token output cap, and thinking disabled where supported. Tasks and original record identifiers:

| Record identifier | Meaning |
|---|---|
| `aquecimento` | Warm-up, excluded from six-response mean |
| `raciocinio` | Arithmetic: three boxes of seven pieces, minus four; expected 17 |
| `codigo` | Python function `unicos`: remove integer duplicates while preserving order |
| `portugues` | Explain RAM versus SSD storage in Portuguese |
| `json` | Return three students and the passing names Ana and Carla as bare JSON |
| `resumo` | Summarize the supplied local-model/SSD passage in three items |
| `planejamento` | Describe five personal-document backup steps |
| `ferramenta` | Additional structured tool-call emission check, excluded from six-response mean |

The generated function passed four recorded cases: empty list; repeated positive values; zero and negative values; and a list with every value equal. Original validators extracted the function from the model output and used a restricted built-in set; this is not a general-purpose sandbox. The publication summary generator does **not** execute model-generated code and reuses the recorded validation outcomes.

Only models advertising tools received the simulated temperature tool. The test checked the emitted call name and city argument, not a live weather query, a tool result round-trip, or end-to-end agent execution.

Some outputs reached the 256-token cap. Reported truncated outputs are retained; a completed function could pass its test cases even when its subsequent explanation was cut off. Models had different weight formats, sizes, quantizations, and execution backends.

## Long-context retrieval

The configured window was increased in stages. A small calibration document estimated tokens per record, then a deterministic synthetic document was generated using seed `20261111`. Filler records describe routine maintenance, reviews, backups, and task verification. Two random ten-letter codes were inserted near each of 3%, 50%, and 97% of document length.

The target formula used 82% of the requested window, but measured occupancy was approximately 83%–86%, due to calibration and tokenization differences. Actual prompt counts are reported separately from configured window sizes. The tests did not fill every available token.

After initial processing of the long document, six queries requested one code each: `BEGIN1`, `BEGIN2`, `MIDDLE1`, `MIDDLE2`, `END1`, and `END2`. A query passed if the expected full code occurred in the returned text; this was substring matching, not a stricter bare-code equality requirement. The warm-up used a 32-token output cap; measured retrievals used 48. The input document was identical within a stage; the question suffix changed. Prefix-cache reuse therefore benefits subsequent queries, unlike a completely new document or substantially changed history.

This is a synthetic exact-retrieval task. Six correct codes do not demonstrate reliable global synthesis, multi-step reasoning, code editing, or instruction-following across the entire window. Different stages used different document lengths and codes; errors in a smaller sample and successes in a larger sample are not evidence that accuracy improves with context length.

## Timing

Decode rate is `eval_count × 1e9 / eval_duration`, using Ollama's nanosecond duration. Tables show the arithmetic mean across six measured calls; the stored short-benchmark summary also includes a token-weighted rate. Loading and prompt processing are excluded from this rate. Request wall time, prompt token count, prompt evaluation duration, and raw response metadata are retained where available.

Long-context answers were very short. Their decode rates are indicative and should not be directly treated as sustained long-form throughput. Initial processing time includes document processing and its warm-up answer, after a separate small calibration has already loaded the model.

The Qwen 262k/q4 initial input was processed in **two segments**, reusing about 107,520 already processed tokens after a client interruption. The reported ~964.9 seconds sums the observed earlier processing segment and resumed request wall time. It is not a single uninterrupted cold-prefill timing. This exception is preserved in the raw record.

## Memory, cache changes, and interruptions

Qwen was tested with the default KV cache, then `q8_0`, then `q4_0`. Quantized-cache server runs used `OLLAMA_FLASH_ATTENTION=1`. These are KV-cache changes; installed model weights were unchanged. Gemma used MLX, and its effective KV-cache type was not confirmed. The GGUF server environment variable must not be assumed to have the same effect on MLX.

System swap and macOS memory-pressure values were observed. Pressure value 1 was treated as normal, 2 as warning, and 4 as critical. Swap values in original records use the `swap_used_mb` field; they come from `sysctl`'s `M` output and are discussed as MiB/GiB in the reports. Swap belongs to the whole system and cannot be attributed exclusively to a model.

High-cost attempts were manually stopped for latency, swap growth, or CPU offload, as explicitly recorded. These are operational cutoffs, not proven absolute hardware limits. The original streaming monitor could begin only after response headers arrived, leaving an early-prefill monitoring gap. The reproduction runner was later adjusted to monitor the open HTTP connection before headers arrive. The full measured battery was not repeated after that change. The adapted public runner includes the adjusted monitoring behavior.

The runner's operational guard uses persistent critical pressure, over 2 GiB of swap growth within a call, or a per-call timeout. The default timeout is 15 minutes; the historic maximum-window continuation allowed 30. This more active guard can stop a reproduction earlier than a historical run.

## Evidence and language

Prompts and model responses retain their original wording, mostly Portuguese. The public JSON retains measured values but excludes identifying metadata. Diagnostic logs and personal preparation material are not distributed. English documentation explains the records, and an English derived summary maps task and status labels. The synthetic long-document filler itself was English, while its instructions and questions were Portuguese.

Tests did not cover images, audio, long-form generation at each large context, real tool execution, full agent workflows, prolonged stability, or independent reruns. Reported model names and hardware versions are local observations.
