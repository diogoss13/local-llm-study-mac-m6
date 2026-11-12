# Results and per-model findings

See [generated tables](RESULTS_TABLES.md) for every recorded stage, including incomplete attempts. The [raw records](../data/raw/) are the measurement source; this report interprets them with identifying metadata removed and experimental response text preserved.

## Qwen 3.5 9B

Exact tag: `qwen3.5:9b-q4_K_M`. Short benchmark: 25.12 mean tokens/s, 23.35–28.02 range, 15.9-second warm-up. It answered the arithmetic task correctly, passed all four function cases, returned bare JSON as requested, and emitted the structured temperature-tool call.

With the default KV cache, it completed all six retrievals at 16k, 32k, and 64k. The 64k run used about 55,770 input tokens, processed the initial document in 108.6 seconds, and averaged 20.52 decode tokens/s. Default-cache 131k was manually stopped after processing was observed near 185 tokens/s with partial CPU offload.

With q8_0 and Flash Attention, it completed 131,072 configured tokens / 111,529 actual input tokens, six correct retrievals, 16.96 decode tokens/s, and approximately 300 seconds initial processing. It ended with normal memory pressure and about 1.2 GiB of system swap. The q8_0 attempt at 262k was stopped after partial offload: about 12.87 GB total reported allocation versus 9.65 GB on GPU.

With q4_0 and Flash Attention, it completed 262,144 configured tokens / approximately 223,073 input tokens, with six correct retrievals and 10.96 decode tokens/s. About 9.2 GB was reported entirely on GPU, with normal final pressure and roughly 1.6 GiB swap. Initial processing accumulated about 964.9 seconds in two segments with prefix reuse; treat it as an approximate accumulated cost, not uninterrupted cold-prefill latency.

This was the strongest observed candidate for maximum context on this machine. The 131k/q8 configuration reduced the initial wait and used less aggressive cache quantization than 262k/q4. Six retrieval checks do not establish equal reasoning quality across cache types.

## Gemma 4 12B

Exact tag: `gemma4:12b`, MLX backend. Short benchmark: 37.92 mean tokens/s, 24.86–47.02 range, 15.4-second warm-up. Arithmetic, four function cases, and structured tool emission passed. Requested bare JSON was wrapped in Markdown. The code function was complete, although its later explanation hit the 256-token cap.

The 16k sample retrieved 5/6 codes; one answer substituted characters. Separate 32k and 64k samples retrieved all six correctly. At 64k, the document contained 56,354 tokens, initial processing took 137.1 seconds, and short-answer decode averaged 15.01 tokens/s. Some suffix changes required approximately 24 seconds of prefix reprocessing.

Memory cost was substantial: around 4.5 GiB of system swap after the 32k queries and 5.6 GiB after 64k, both with warning-level pressure. The 131k attempt was manually stopped during prefill, around 88,064 of 112,703 planned input tokens, with approximately 4.5 GiB swap. There was no full retrieval result at 131k. Therefore 64k is its largest fully completed stage here, **not a proven maximum**. Effective MLX KV-cache precision was not confirmed.

## Qwen Coder 14B

Exact tag: `qwen2.5-coder:14b`. Short benchmark: 15.54 mean tokens/s, 15.00–17.04 range, 23.8-second warm-up. Arithmetic and the four function cases passed. Bare JSON was wrapped in Markdown; the planning answer reached the output cap. The tool request appeared as plain JSON text rather than a structured `tool_calls` entry. This observation concerns the tested model/runtime integration, not proof of universal lack of tool ability.

With q4_0, both 16k and its declared maximum of 32,768 passed six retrievals. The maximum run contained 27,513 input tokens, took 124.6 seconds for initial processing, and averaged 10.97 decode tokens/s. Final memory pressure was normal; system swap was about 1.9 GiB. No context above its recorded native maximum was requested.

## DeepSeek Coder V2 16B

Exact tag: `deepseek-coder-v2:16b`. Short benchmark: 78.94 mean tokens/s, 77.78–81.99 range, 21.7-second warm-up. It passed arithmetic and the four function cases. However, it ignored the single-sentence arithmetic instruction, wrapped requested JSON in Markdown, and misread SSD storage as Single Shot MultiBox Detector, inventing an object-detection project in its summary. The summary reached the output cap. No tool test was sent because its advertised capabilities omitted tools.

The 16k retrieval sample scored 4/6, repeating another entry's code for two questions. The separate 32k sample passed all six: 27,274 input tokens, 34.7-second initial processing, and 35.36 decode tokens/s. These differences illustrate sample-dependent outcomes, not a monotonic accuracy trend.

The 64k attempt was stopped after about 14.86 GB total Ollama allocation, around 11.64 GB on GPU, partial CPU offload, warning-level pressure, and about 3.7 GiB swap. It did not complete a retrieval stage at 64k. Its declared 163,840-token maximum was not established as practically usable.

## Interpretation

The larger windows require matching server cache settings and per-request context settings. No model weights were changed. Images, audio, real tool execution, sustained multi-day stability, and complete agent workflows were not evaluated.

Use these measurements to choose further tests for the intended workload. Exact code retrieval and six short tasks are insufficient to certify large-document reasoning or reliable autonomous editing.
