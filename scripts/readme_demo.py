"""Run the unchanged legacy API against three invented records in a temporary directory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_SHA256 = "d8560c3592aa1df9779f2168b0a31e510982c681e10e86043468473c41bdf09f"
SCORES = (3, 4, 5)


def run_demo() -> tuple[dict, str, str]:
    archive = ROOT / "evtalbert_v0_1_0.zip"
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError("The legacy archive changed; review the new source before updating this demo.")
    with tempfile.TemporaryDirectory(prefix="evtalbert-readme-") as directory:
        temporary = Path(directory)
        package = temporary / "src" / "evtalbert"
        package.mkdir(parents=True)
        # Copy only reviewed Python source files. No legacy bytecode or data is loaded.
        with zipfile.ZipFile(archive) as bundle:
            for name in ("__init__.py", "models.py", "storage.py", "analytics.py"):
                (package / name).write_bytes(bundle.read("src/evtalbert/" + name))
        sys.path.insert(0, str(temporary / "src"))
        from evtalbert.analytics import compute_metrics, write_markdown
        from evtalbert.models import Outcome, PreStartState, SessionEntry
        from evtalbert.storage import append_jsonl, export_csv, get_paths

        workspace = temporary / "synthetic-workspace"
        entries = []
        for index, (score, state, seconds, outcome, obstacle) in enumerate(zip(
            SCORES,
            (PreStartState.ALERT, PreStartState.FEVER, PreStartState.ALERT),
            (20, 40, None),
            (Outcome.SUCCESS, Outcome.PARTIAL, Outcome.SUCCESS),
            ("time-pressure", "equipment", "time-pressure"),
        ), start=1):
            entry = SessionEntry(
                ts=f"2025-01-{index:02d}T10:00:00Z", athlete="synthetic-demo",
                sport="fictional-task", task=f"example-{index}", pre_state=state,
                regulation="invented-demo-label", sec_to_target=seconds, obstacle=obstacle,
                outcome=outcome, rpe=None,
                volition={key: score for key in ("purposefulness", "persistence", "self_control", "decisiveness")},
                notes="Entirely invented documentation fixture; no person or study participant.",
            ).to_dict()
            entries.append(entry)
            append_jsonl(get_paths(workspace)["logs_file"], entry)
        metrics = compute_metrics(workspace)
        raw_report = write_markdown(workspace, metrics).read_text(encoding="utf-8")
        exported_rows = export_csv(workspace, temporary / "synthetic.csv")
        csv_text = (temporary / "synthetic.csv").read_text(encoding="utf-8")
        if len(list(csv.DictReader(io.StringIO(csv_text)))) != exported_rows:
            raise RuntimeError("CSV row count does not match the actual export.")
        result = {
            "fixture": "three invented records; no personal or health data",
            "archive_sha256": digest,
            "session_rating_means": list(SCORES),
            "metrics": metrics,
            "csv_rows": exported_rows,
            "legacy_markdown_has_literal_backslash_n": "\\n" in raw_report,
        }
        return result, csv_text, raw_report


def diagram(result: dict) -> str:
    m = result["metrics"]
    labels = [
        ("Records", str(m["total_sessions"])),
        ("ALERT-coded starts", f"{m['readiness_ratio'] * 100:.1f}%"),
        ("Mean recorded time", f"{m['avg_sec_to_target']:.0f} s"),
        ("Proposed rolling VI", f"{m['latest_vi']:.2f}"),
        ("Outcomes", f"{m['outcome_counts']['success']} success / {m['outcome_counts']['partial']} partial"),
        ("CSV rows exported", str(result["csv_rows"])),
    ]
    rows = "".join(f'<text x="660" y="{143+i*43}" font-size="19" fill="#475569">{label}</text><text x="1125" y="{143+i*43}" font-size="24" text-anchor="end" fill="#0f172a">{value}</text>' for i, (label, value) in enumerate(labels))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="460" viewBox="0 0 1200 460" role="img" aria-labelledby="title desc">
<title id="title">EVT-Albert: observed synthetic session-to-summary demo</title>
<desc id="desc">Three invented sessions produce three records, 66.7 percent ALERT-coded starts, 30 seconds mean recorded time, rolling proposed VI 4.00, two success and one partial labels, and three exported CSV rows. These are computations on a fixture, not scientific validation.</desc>
<rect width="1200" height="460" rx="14" fill="#f4f7fb"/>
<g font-family="Arial, Helvetica, sans-serif">
<text x="42" y="50" font-size="16" letter-spacing="2" fill="#46627d">RUNNABLE DEMO · SYNTHETIC INPUT ONLY</text>
<text x="40" y="91" font-size="30" font-weight="bold" fill="#0f172a">Three sessions → one computed summary</text>
<rect x="40" y="113" width="510" height="260" rx="12" fill="#ffffff" stroke="#d6e0eb"/>
<text x="63" y="147" font-size="20" font-weight="bold" fill="#1f3d58">Input supplied to the archived API</text>
<text x="63" y="193" font-size="20" fill="#334155">A: alertness · 20 s · success · ratings all 3</text>
<text x="63" y="239" font-size="20" fill="#334155">B: fever code · 40 s · partial · ratings all 4</text>
<text x="63" y="285" font-size="20" fill="#334155">C: alertness · no time · success · ratings all 5</text>
<text x="63" y="337" font-size="17" fill="#64748b">Labels and ratings are invented, not observations.</text>
<path d="M575 243 H620 M610 233 L621 243 L610 253" fill="none" stroke="#517b9e" stroke-width="3"/>
{rows}
<text x="42" y="412" font-size="18" fill="#334155">The proposed VI averages supplied ratings, then takes a trailing mean over up to 7 sessions.</text>
<text x="42" y="440" font-size="17" fill="#64748b">Exploratory software output; no psychological, clinical or theoretical validity is established.</text>
</g></svg>\n'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-assets", action="store_true", help="Regenerate the tracked synthetic documentation outputs.")
    args = parser.parse_args()
    result, csv_text, raw_report = run_demo()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write_assets:
        out = ROOT / "docs" / "demo"
        out.mkdir(parents=True, exist_ok=True)
        (out / "output.json").write_text(text, encoding="utf-8")
        (out / "synthetic.csv").write_text(csv_text, encoding="utf-8")
        (out / "legacy-report.txt").write_text(raw_report, encoding="utf-8")
        (out / "demo.svg").write_text(diagram(result), encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
