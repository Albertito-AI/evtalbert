# Synthetic session-to-summary demonstration

This example runs the existing code preserved in `evtalbert_v0_1_0.zip`. All
records are invented solely for documentation; there is no participant, patient,
athlete or actual performance history behind them.

## Reproduce

From the repository root, using Python 3.10 or later:

```bash
python scripts/readme_demo.py
```

Only the standard library is required. The script verifies the archive digest,
copies the four reviewed package source files into a fresh temporary directory,
and calls the existing `SessionEntry`, `append_jsonl`, `compute_metrics`,
`write_markdown` and `export_csv` APIs. It loads no bundled bytecode or existing
records. The workspace is removed when the command finishes.

To regenerate the checked-in JSON, CSV, raw report and SVG:

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
rating. The existing implementation averages those values per session, then
averages up to seven recent session means. Here the rolling series is
`[3.0, 3.5, 4.0]`. Two of three rows use the `alertness` code, and the mean of
the two recorded times is `(20 + 40) / 2 = 30` seconds.

- [Actual metrics JSON](output.json)
- [Actual three-row synthetic CSV export](synthetic.csv)
- [Raw legacy report output](legacy-report.txt)
- [Data-derived SVG](demo.svg)

The legacy Markdown writer currently joins lines using literal backslash-n
characters (`\n`). The raw output is preserved exactly in `legacy-report.txt`;
the visual reads the computed metrics directly. This demo does not repair or
conceal that formatting defect. The CSV export does not establish anonymity
or the safety of publishing real records.

## Provenance and limits

Observed with Python 3.12.14 on Linux. The runtime was read from source commit
[`5cc697e8aa5dc486b85843d4e939dc6dba0a650a`](https://github.com/Albertito-AI/evtalbert/commit/5cc697e8aa5dc486b85843d4e939dc6dba0a650a).
The preserved archive's SHA-256 is
`d8560c3592aa1df9779f2168b0a31e510982c681e10e86043468473c41bdf09f`.
The generator rejects a different archive until its source is reviewed.

The source archive, runtime and licence are unchanged. This is evidence that
these specific inputs produce the recorded software output. It is not evidence
of a psychological construct, clinical usefulness, real-world performance,
privacy assurance or scientific validation.
