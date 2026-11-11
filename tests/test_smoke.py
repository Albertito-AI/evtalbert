import subprocess, sys, os, tempfile, json, pathlib

def run_cli(args, cwd):
    cmd = [sys.executable, "-m", "evtalbert.cli"] + args
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return res.stdout

def test_flow(tmp_path):
    # install package should be done by CI; here we just call module directly
    proj = tmp_path
    out = run_cli(["init","--root", str(proj)], cwd=proj)
    assert "Initialized workspace" in out

    out = run_cli([
        "log-session",
        "--athlete","albert",
        "--sport","moot-court",
        "--task","hot-seat",
        "--pre-state","fever",
        "--regulation","breath",
        "--sec-to-target","30",
        "--obstacle","hostile-question",
        "--outcome","success",
        "--rpe","7",
        "--v","purposefulness=4,persistence=5,self_control=4,decisiveness=4",
        "--notes","ok",
        "--root", str(proj)
    ], cwd=proj)
    assert "Logged session" in out

    out = run_cli(["report","--root", str(proj)], cwd=proj)
    assert "Wrote analytics" in out