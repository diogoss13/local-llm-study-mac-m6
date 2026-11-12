# Test hardware and models

Specifications were reported by local system tools. Device identifiers, volume labels, mount paths, display information, firmware details, and unrelated peripheral information are excluded.

| Component | Configuration |
|---|---|
| Computer | Mac mini |
| CPU | Apple M6, 12 cores: 2 Super, 4 Performance, 6 Efficiency |
| GPU | Integrated Apple M6 GPU, 12 cores, Metal 4 |
| Unified memory | 16 GB |
| Operating system | macOS 27.2.1, build 26B131 |
| External storage | E300 SSD, nominally 512 GB, ExFAT |
| USB link | 10 Gb/s after cable replacement |
| Ollama | 0.40.15 |
| MLX engine | 0.32.4-43-g54a7051 |
| Python | 3.9.6, standard library |

Ollama reported about 11.8 GiB as the GPU recommended working-set capacity. Unified memory is shared with the operating system and applications; it is not separate dedicated VRAM. Other applications remained open, and swap was not reset between every run.

## Storage observation

The external SSD initially negotiated a 480 Mb/s USB link. Approximately 38 MB/s was observed with `iostat` during model loading. After replacing the cable, it negotiated 10 Gb/s. A read-only sequential test used 8 MiB blocks and macOS `F_NOCACHE`:

- Data read: 1,073,741,824 bytes (1 GiB).
- Elapsed time: 1.981 seconds.
- Throughput: 542.1 decimal MB/s, or 517.0 MiB/s.

There was no write-speed test. The before/after methods differed, so the observation is diagnostic rather than a controlled storage benchmark. See [storage.json](../environment/storage.json).

## Models

| Exact tag | Reported parameters | Weight format / quantization | Disk size, decimal GB | Declared context |
|---|---:|---|---:|---:|
| `qwen3.5:9b-q4_K_M` | 9.0B | GGUF / Q4_K_M | 6.55 | 262,144 |
| `gemma4:12b` | 12B in tag; count absent from metadata | safetensors / MLX; quantization unspecified | 7.71 | 262,144 |
| `qwen2.5-coder:14b` | 14.8B | GGUF / Q4_K_M | 8.99 | 32,768 |
| `deepseek-coder-v2:16b` | 15.7B | GGUF / Q4_0 | 8.91 | 163,840 |

[models.json](../environment/models.json) contains exact model digests, sizes, and advertised capabilities. Declared context is metadata, not proof of fit or accuracy. [hardware.json](../environment/hardware.json) contains the relevant technical environment without machine-specific identifiers.
