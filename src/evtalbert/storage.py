from __future__ import annotations
import json, os, csv, hashlib
from pathlib import Path
from typing import Iterable, Dict, Any, List, Optional

DEFAULT_DATA_DIR = "data/logs"
CONFIG_FILE = "config.json"

def get_paths(root: Path) -> Dict[str, Path]:
    data_dir = root / DEFAULT_DATA_DIR
    logs_file = data_dir / "logs.jsonl"
    analytics_file = data_dir / "analytics.md"
    config_file = root / CONFIG_FILE
    return {
        "data_dir": data_dir,
        "logs_file": logs_file,
        "analytics_file": analytics_file,
        "config_file": config_file,
    }

def ensure_dirs(root: Path) -> None:
    paths = get_paths(root)
    paths["data_dir"].mkdir(parents=True, exist_ok=True)

def init_config(root: Path) -> None:
    ensure_dirs(root)
    cfg_path = get_paths(root)["config_file"]
    if cfg_path.exists():
        return
    salt = os.urandom(16).hex()
    cfg = {"version": "0.1.0", "anonymize_salt": salt, "publish_raw_logs": False}
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def read_config(root: Path) -> Dict[str, Any]:
    cfg_path = get_paths(root)["config_file"]
    if not cfg_path.exists():
        init_config(root)
    return json.loads(cfg_path.read_text(encoding="utf-8"))

def append_jsonl(file: Path, obj: Dict[str, Any]) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def iter_jsonl(file: Path) -> Iterable[Dict[str, Any]]:
    if not file.exists():
        return []
    with file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def anonymize(text: str, salt: str) -> str:
    return hashlib.sha256((salt + "|" + text).encode("utf-8")).hexdigest()[:16]

def export_csv(root: Path, out_path: Path, anonymize_names: bool = False) -> int:
    from .storage import get_paths, read_config, iter_jsonl
    paths = get_paths(root)
    cfg = read_config(root)
    rows = list(iter_jsonl(paths["logs_file"]))
    if anonymize_names:
        for r in rows:
            r["athlete"] = anonymize(r.get("athlete", ""), cfg["anonymize_salt"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        # write header only
        headers = ["ts","athlete","sport","task","pre_state","regulation","sec_to_target","obstacle","outcome","rpe","volition","notes"]
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return 0
    headers = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return len(rows)