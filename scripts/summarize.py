#!/usr/bin/env python3
"""Rebuild English summaries from bundled historical records; no inference or code execution."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = {
    'aquecimento': 'warm_up', 'raciocinio': 'arithmetic', 'codigo': 'code',
    'portugues': 'portuguese_explanation', 'json': 'json', 'resumo': 'summary',
    'planejamento': 'planning', 'ferramenta': 'tool_call',
}
VALIDATION = {
    'ok': 'passed', 'ok: 4 casos': 'passed_four_cases',
    'dados corretos, mas envoltos em Markdown': 'correct_data_wrapped_in_markdown',
    'sem chamada estruturada': 'no_structured_tool_call',
    'revisão textual': 'text_review', 'erro': 'error', 'falhou': 'failed',
}
STATUS = {
    'ok': 'completed_all_retrievals_correct', 'retrieval_failed': 'completed_with_retrieval_errors',
    'error': 'error', 'interrompido_por_lentidao': 'stopped_for_latency',
    'interrompido_por_offload': 'stopped_for_cpu_offload',
    'interrompido_por_memoria_offload': 'stopped_for_memory_and_cpu_offload',
    'interrompido_por_swap': 'stopped_for_swap_growth',
}
STAGES = [
    ('default-cache', 'default'), ('q8-cache', 'q8_0'), ('q4-cache', 'q4_0'),
    ('other-models', 'q4_0'), ('confirmation', 'q4_0'), ('gemma-limit', 'MLX'),
]


def load(path):
    return json.loads((ROOT / path).read_text())


def build():
    raw = load('data/raw/short-context/results.json')
    validated = load('data/derived/benchmark-validation.json')
    recorded_validation = {
        (row['model'], row['test']): row.get('validation')
        for row in validated['results']
    }
    short = []
    for model in dict.fromkeys(row['model'] for row in raw):
        group = [row for row in raw if row['model'] == model]
        measured = [row for row in group if row.get('measured') and row.get('tokens_per_second')]
        rates = [row['tokens_per_second'] for row in measured]
        token_count = sum(row['response']['eval_count'] for row in measured)
        duration = sum(row['response']['eval_duration'] for row in measured) / 1e9
        short.append({
            'model': model, 'measured_responses': len(measured),
            'mean_tokens_per_second': round(statistics.mean(rates), 2),
            'min_tokens_per_second': min(rates), 'max_tokens_per_second': max(rates),
            'weighted_tokens_per_second': round(token_count / duration, 2),
            'warm_up_seconds': next(row['seconds'] for row in group if row['test'] == 'aquecimento'),
            'recorded_validation': {
                TASKS.get(row['test'], row['test']): VALIDATION.get(
                    recorded_validation.get((model, row['test'])),
                    recorded_validation.get((model, row['test']))
                ) for row in group if row['test'] in ('codigo', 'raciocinio', 'json', 'ferramenta')
            },
            'output_cap_reached': [TASKS.get(row['test'], row['test']) for row in group
                                   if row.get('response', {}).get('done_reason') == 'length'],
        })
    long = []
    for stage, cache in STAGES:
        source = f'data/raw/long-context/{stage}.json'
        for row in load(source):
            tests = row.get('tests', [])
            rates = [test['tokens_per_second'] for test in tests if test.get('tokens_per_second')]
            prefill = row.get('prefill', {})
            actual = row.get('actual_context')
            stopped_models = row.get('loaded_models_at_stop', {}).get('models', [])
            if actual is None and stopped_models:
                actual = stopped_models[0].get('context_length')
            long.append({
                'source': source, 'model': row['model'],
                'cache_configuration': 'MLX; effective KV precision unconfirmed'
                if row['model'].startswith('gemma') else cache,
                'requested_context_tokens': row['requested_context'],
                'allocated_context_tokens': actual,
                'input_tokens': prefill.get('prompt_tokens'),
                'initial_processing_seconds': prefill.get('seconds'),
                'initial_processing_is_segmented': bool(row.get('initial_processing_segment')),
                'partial_input_tokens_observed': row.get('partial_prefill_tokens_observed'),
                'correct_retrievals': sum(test['passed'] for test in tests),
                'completed_queries': len(tests),
                'mean_tokens_per_second': round(statistics.mean(rates), 2) if rates else None,
                'status': STATUS.get(row.get('status'), row.get('status', 'in_progress')),
                'original_error_note': row.get('error'),
                'final_or_last_memory': row.get('memory_after_tests',
                    row.get('memory_at_stop', row.get('memory_after_load'))),
            })
    return {'study_date': '2026-11-11', 
            'short_context': short, 'long_context': long}


def render(summary):
    lines = ['# Recorded results: generated tables', '',
             'Generated by `scripts/summarize.py` from privacy-filtered study JSON. '
             'Incomplete stages are not counted as successful retrieval tests. '
             'See [methodology](METHODOLOGY.md) for qualifications.', '',
             '## Short context', '',
             '| Model | Measured responses | Mean tokens/s | Min–max | Warm-up (s) |',
             '|---|---:|---:|---:|---:|']
    for row in summary['short_context']:
        lines.append(f"| {row['model']} | {row['measured_responses']} | "
                     f"{row['mean_tokens_per_second']} | {row['min_tokens_per_second']}–"
                     f"{row['max_tokens_per_second']} | {row['warm_up_seconds']} |")
    lines += ['', '## Long context', '',
              '| Model / cache | Window | Actual input | Initial processing (s) | Correct/queried | Mean tokens/s | Status |',
              '|---|---:|---:|---:|---:|---:|---|']
    for row in summary['long_context']:
        def value(key):
            result = row[key]
            return '—' if result is None else result
        segmented = ' (segmented)' if row['initial_processing_is_segmented'] else ''
        lines.append(f"| {row['model']} / {row['cache_configuration']} | "
                     f"{row['requested_context_tokens']} | {value('input_tokens')} | "
                     f"{value('initial_processing_seconds')}{segmented} | "
                     f"{row['correct_retrievals']}/{row['completed_queries']} | "
                     f"{value('mean_tokens_per_second')} | {row['status']} |")
    lines += ['', 'A 0/0 result means no measured retrieval queries completed, not zero accuracy. '
              'Configured context and actual input counts are different quantities. '
              'Long-context rates are based on short code-retrieval answers. '
              'Original error annotations remain in Portuguese in the raw records and English summary JSON.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    summary = build()
    output = ROOT / 'data/derived/summary.en.json'
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    (ROOT / 'docs/RESULTS_TABLES.md').write_text(render(summary))
    print('Updated data/derived/summary.en.json and docs/RESULTS_TABLES.md (offline).')
