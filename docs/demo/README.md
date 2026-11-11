# Synthetic session-to-summary demonstration

This example runs the inspectable code under `src/evtalbert`. All records are
invented solely for documentation; there is no participant, patient, athlete or
actual performance history behind them.

## Reproduce

From the repository root, using Python 3.10 or later:

```bash
python scripts/readme_demo.py
python scripts/readme_demo.py --check
```

Only the standard library is required. The script records the hashes of the five
source modules and calls `SessionEntry`, `append_jsonl`, `compute_metrics`,
`write_markdown` and `export_csv` with a fresh temporary workspace. It reads no
existing records. The workspace is removed when the command finishes. The check
compares actual outputs with the four committed demonstration artifacts byte
for byte. The CSV retains its exported CRLF line endings. The recorded replay
environment is Linux; reports use the platform's native line endings.

To regenerate those JSON, CSV, Markdown and SVG artifacts after reviewing a
source change:

```bash
python scripts/readme_demo.py --write-assets
```

## Input and observed output

| Invented session | `pre_state` code | Recorded seconds | Outcome label | Each of four supplied ratings |
| --- | --- | --- | --- | --- |
| A | `alertness` | 20 | `success` | 3 |
| B | `fever` | 40 | `partial` | 4 |
| C | `alertness` | absent | `success` | 5 |

These are literal schema labels, not clinical findings. Each row supplies
purposefulness, persistence, self-control and decisiveness with the stated
rating. The implementation averages those values per session, then averages up
to seven recent session means. Here the rolling series is `[3.0, 3.5, 4.0]`.
Two of three rows use the `alertness` code, and the mean of the two recorded times
is `(20 + 40) / 2 = 30` seconds.

- [Actual metrics JSON and source hashes](output.json)
- [Actual three-row synthetic CSV export](synthetic.csv)
- [Current Markdown report](report.md)
- [Data-derived SVG](demo.svg)
- [Preserved historical report with literal backslash-n separators](legacy-report.txt)

The source migration fixed the writer's literal backslash-n separators (`\n`)
to real line breaks. The historical report remains unchanged as evidence of
the earlier behaviour; current reports and the visual use the same computed
metrics. The CSV export does not establish anonymity or the safety of publishing
real records.

## Provenance and limits

The corrected demonstration was observed with Python 3.12.14 on Linux on
11 November 2026. [The source-migration record](../SOURCE_MIGRATION.md) and
[original archive manifest](../legacy-source-manifest.json) identify the exact
baseline and the one-line runtime correction. The metric definitions and the
root MIT licence are unchanged.

This is evidence that these specific inputs produce the recorded software
output. It is not evidence of a psychological construct, clinical usefulness,
real-world performance, privacy assurance or scientific validation.
