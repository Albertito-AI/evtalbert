from __future__ import annotations
import argparse, sys, json, re
from pathlib import Path
from typing import Dict, Any, Optional

from .models import PreStartState, Outcome, SessionEntry, now_iso
from .storage import get_paths, ensure_dirs, init_config, read_config, append_jsonl, export_csv
from .analytics import compute_metrics, write_markdown

def _root(p: Optional[str]) -> Path:
    return Path(p or ".").resolve()

def cmd_init(args: argparse.Namespace) -> int:
    root = _root(args.root)
    ensure_dirs(root)
    init_config(root)
    paths = get_paths(root)
    print(f"[OK] Initialized workspace at {root}")
    print(f"[OK] Data dir: {paths['data_dir']}")
    print(f"[OK] Config:   {paths['config_file']}")
    return 0

def parse_volition(s: str) -> Dict[str, int]:
    # e.g., "purposefulness=4,persistence=5,self_control=4,decisiveness=4"
    out: Dict[str, int] = {}
    if not s:
        return out
    for part in s.split(","):
        if not part.strip():
            continue
        if "=" not in part:
            raise ValueError(f"Bad volition token: {part}")
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not v.isdigit():
            raise ValueError(f"Non-integer volition score for {k}: {v}")
        out[k] = int(v)
    return out

def cmd_log_session(args: argparse.Namespace) -> int:
    root = _root(args.root)
    ensure_dirs(root); init_config(root)
    paths = get_paths(root)
    entry = SessionEntry(
        ts=now_iso(),
        athlete=args.athlete,
        sport=args.sport,
        task=args.task,
        pre_state=PreStartState(args.pre_state),
        regulation=args.regulation,
        sec_to_target=float(args.sec_to_target) if args.sec_to_target is not None else None,
        obstacle=args.obstacle,
        outcome=Outcome(args.outcome),
        rpe=int(args.rpe) if args.rpe is not None else None,
        volition=parse_volition(args.v or ""),
        notes=args.notes,
    )
    append_jsonl(paths["logs_file"], entry.to_dict())
    print(f"[OK] Logged session to {paths['logs_file']}")
    return 0

def cmd_report(args: argparse.Namespace) -> int:
    root = _root(args.root)
    ensure_dirs(root); init_config(root)
    m = compute_metrics(root)
    out = write_markdown(root, m)
    print(f"[OK] Wrote analytics to {out}")
    return 0

def cmd_export(args: argparse.Namespace) -> int:
    root = _root(args.root)
    ensure_dirs(root); init_config(root)
    n = export_csv(root, Path(args.path), anonymize_names=args.anonymize)
    print(f"[OK] Exported {n} rows to {args.path}")
    return 0

def cmd_synthetic(args: argparse.Namespace) -> int:
    import random
    root = _root(args.root)
    ensure_dirs(root); init_config(root)
    paths = get_paths(root)
    states = [s.value for s in PreStartState]
    outcomes = [o.value for o in Outcome]
    obstacles = ["crowd-noise","bad-call","equipment","time-pressure","hostile-question"]
    for i in range(args.n):
        v = {
            "purposefulness": random.randint(3,5),
            "persistence": random.randint(3,5),
            "self_control": random.randint(3,5),
            "decisiveness": random.randint(3,5),
        }
        entry = {
            "ts": "2025-01-{:02d}T10:00:00Z".format((i%28)+1),
            "athlete": "demo",
            "sport": "demo",
            "task": f"drill-{i%5}",
            "pre_state": random.choices(states, weights=[0.5,0.3,0.2])[0],
            "regulation": "breath-4-2-6 + cue",
            "sec_to_target": random.choice([None, random.randint(10,60)]),
            "obstacle": random.choice(obstacles),
            "outcome": random.choices(outcomes, weights=[0.6,0.25,0.15])[0],
            "rpe": random.randint(4,8),
            "volition": v,
            "notes": None,
        }
        append_jsonl(paths["logs_file"], entry)
    print(f"[OK] Generated {args.n} synthetic entries at {paths['logs_file']}")
    return 0

def main(argv: Optional[list[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="evtalbert", description="EVT-Albert CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="initialize workspace")
    pi.add_argument("--root", help="project root (default: .)")
    pi.set_defaults(func=cmd_init)

    pl = sub.add_parser("log-session", help="log a training/competition session")
    pl.add_argument("--athlete", required=True)
    pl.add_argument("--sport", required=True)
    pl.add_argument("--task", required=True)
    pl.add_argument("--pre-state", choices=[s.value for s in PreStartState], required=True)
    pl.add_argument("--regulation", required=True)
    pl.add_argument("--sec-to-target", type=float)
    pl.add_argument("--obstacle", required=True)
    pl.add_argument("--outcome", choices=[o.value for o in Outcome], required=True)
    pl.add_argument("--rpe", type=int)
    pl.add_argument("--v", help="volition scores e.g. purposefulness=4,persistence=5,self_control=4,decisiveness=4")
    pl.add_argument("--notes")
    pl.add_argument("--root", help="project root (default: .)")
    pl.set_defaults(func=cmd_log_session)

    pr = sub.add_parser("report", help="compute analytics and write markdown")
    pr.add_argument("--root", help="project root (default: .)")
    pr.set_defaults(func=cmd_report)

    pe = sub.add_parser("export", help="export CSV")
    pe.add_argument("--path", required=True, help="output CSV path")
    pe.add_argument("--anonymize", action="store_true", help="anonymize athlete identifiers")
    pe.add_argument("--root", help="project root (default: .)")
    pe.set_defaults(func=cmd_export)

    ps = sub.add_parser("synthetic", help="generate synthetic demo data")
    ps.add_argument("--n", type=int, default=30)
    ps.add_argument("--root", help="project root (default: .)")
    ps.set_defaults(func=cmd_synthetic)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())