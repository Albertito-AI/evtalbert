from __future__ import annotations
from typing import Dict, Any
from pathlib import Path

from .storage import get_paths, iter_jsonl

def compute_metrics(root: Path) -> Dict[str, Any]:
    paths = get_paths(root)
    rows = list(iter_jsonl(paths["logs_file"]))
    n = len(rows)
    if n == 0:
        return {
            "total_sessions": 0,
            "readiness_ratio": None,
            "avg_sec_to_target": None,
            "outcome_counts": {},
            "vi_series": [],
            "latest_vi": None,
            "top_obstacles": [],
        }
    # Readiness: pre_state == alertness
    ready = sum(1 for r in rows if r.get("pre_state") == "alertness")
    readiness_ratio = ready / n if n else None

    # Average sec_to_target
    secs = [float(r["sec_to_target"]) for r in rows if r.get("sec_to_target") is not None]
    avg_sec = sum(secs)/len(secs) if secs else None

    # Outcome mix
    outcome_counts: Dict[str, int] = {}
    for r in rows:
        oc = r.get("outcome")
        if oc:
            outcome_counts[oc] = outcome_counts.get(oc, 0) + 1

    # VI rolling mean (7-session)
    def vi_from_volition(v: Dict[str, int]) -> float:
        if not v:
            return 0.0
        vals = []
        for k in ("purposefulness","persistence","self_control","decisiveness"):
            if k in v:
                vals.append(float(v[k]))
        return sum(vals)/len(vals) if vals else 0.0

    vis = [vi_from_volition(r.get("volition", {})) for r in rows]
    window = 7
    vi_series = []
    for i in range(len(vis)):
        s = vis[max(0, i-window+1): i+1]
        vi_series.append(sum(s)/len(s))
    latest_vi = vi_series[-1] if vi_series else None

    # Top obstacles
    from collections import Counter
    counts = Counter(r.get("obstacle","").split(":")[0].strip().lower() for r in rows if r.get("obstacle"))
    top_obstacles = counts.most_common(5)

    return {
        "total_sessions": n,
        "readiness_ratio": readiness_ratio,
        "avg_sec_to_target": avg_sec,
        "outcome_counts": outcome_counts,
        "vi_series": vi_series,
        "latest_vi": latest_vi,
        "top_obstacles": top_obstacles,
    }

def write_markdown(root: Path, m: Dict[str, Any]) -> Path:
    paths = get_paths(root)
    out = paths["analytics_file"]
    out.parent.mkdir(parents=True, exist_ok=True)

    def pct(x):
        return f"{x*100:.1f}%" if x is not None else "n/a"

    def fmt(x):
        if x is None:
            return "n/a"
        if isinstance(x, float):
            return f"{x:.2f}"
        return str(x)

    lines = []
    lines.append("# EVT‑Albert Analytics")
    lines.append("")
    lines.append(f"- **Total sessions:** {m['total_sessions']}")
    lines.append(f"- **Readiness ratio (ALERT starts):** {pct(m['readiness_ratio'])}")
    lines.append(f"- **Average sec to target:** {fmt(m['avg_sec_to_target'])}")
    oc = m['outcome_counts']
    lines.append(f"- **Outcome mix:** success={oc.get('success',0)}, partial={oc.get('partial',0)}, failure={oc.get('failure',0)}")
    lines.append(f"- **Latest VI (7-session mean):** {fmt(m['latest_vi'])}")
    lines.append("")
    lines.append("## Top Obstacles")
    if not m["top_obstacles"]:
        lines.append("_None yet._")
    else:
        for k, c in m["top_obstacles"]:
            lines.append(f"- {k or 'unspecified'}: {c}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
