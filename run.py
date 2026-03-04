# run.py
# Single entry-point for the full fx_regime pipeline.
# Replaces run_all.py with argparse, per-step timing, and clean error output.
#
# Usage:
#   python run.py                          # run all steps
#   python run.py --skip deploy            # skip git push
#   python run.py --only html              # re-build HTML brief only
#   python run.py --only cot inr merge    # refresh COT + INR data, rebuild merge
#   python run.py --skip cot inr          # skip slow network steps
#
# Step names: fx  yields  cot  inr  merge  text  html  deploy

import sys
import os
import glob
import shutil
import subprocess
import argparse
import time
from datetime import datetime

# ── pipeline step definitions ─────────────────────────────────────────────────
# Each entry: (name, script_file)
# Order matters — each step may depend on the output of the previous one.
STEPS = [
    ("fx",      "pipeline.py"),           # fetch FX prices + yields → data/latest.csv
    ("cot",     "cot_pipeline.py"),       # fetch CFTC COT data → data/cot_latest.csv
    ("inr",     "inr_pipeline.py"),       # fetch USD/INR + IN yields → data/inr_latest.csv
    ("merge",   "pipeline.py"),           # NOTE: merge is part of pipeline.py (same script)
    ("text",    "morning_brief.py"),      # generate text brief → briefs/brief_YYYYMMDD.txt
    ("html",    "create_html_brief.py"),  # generate HTML brief → briefs/brief_YYYYMMDD.html
    ("deploy",  "deploy.py"),             # copy to index.html and push to GitHub
]

# Deduplicated step scripts (some names share a script — merge is inside pipeline.py)
# When --only merge is requested, pipeline.py still runs (the merge phase is its final step).
_STEP_NAMES = [name for name, _ in STEPS]


def _run_step(name, script, python_exe):
    """Run one pipeline step.  Returns (success: bool, elapsed_seconds: float)."""
    t0 = time.perf_counter()
    result = subprocess.run([python_exe, script], capture_output=False)
    elapsed = time.perf_counter() - t0
    return result.returncode == 0, elapsed


def _archive(today_str):
    """Archive run outputs into runs/YYYY-MM-DD/."""
    run_dir = os.path.join('runs', today_str)
    os.makedirs(os.path.join(run_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(run_dir, 'charts'), exist_ok=True)

    slug = today_str.replace('-', '')
    file_map = {
        f'data/master_{slug}.csv':       'master.csv',
        'data/cot_latest.csv':           'cot.csv',
        'data/latest_with_cot.csv':      'master_with_cot.csv',
        f'briefs/brief_{slug}.html':     'brief.html',
    }
    for src, dst_name in file_map.items():
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(run_dir, 'data', dst_name))

    brief_txt = f'briefs/brief_{slug}.txt'
    if os.path.exists(brief_txt):
        shutil.copy2(brief_txt, os.path.join(run_dir, 'brief.txt'))

    # Copy chart HTML files so the archived brief is self-contained
    for chart_file in glob.glob('charts/*.html'):
        shutil.copy2(chart_file, os.path.join(run_dir, 'charts', os.path.basename(chart_file)))

    print(f'  archived -> runs/{today_str}/')


def main():
    parser = argparse.ArgumentParser(
        description='fx_regime daily pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'Available steps: {", ".join(_STEP_NAMES)}'
    )
    parser.add_argument(
        '--skip', nargs='*', default=[], metavar='STEP',
        help='Steps to skip (space-separated)'
    )
    parser.add_argument(
        '--only', nargs='*', default=None, metavar='STEP',
        help='Run only these steps (space-separated)'
    )
    args = parser.parse_args()

    # Validate step names
    all_names = set(_STEP_NAMES)
    for n in (args.skip or []) + (args.only or []):
        if n not in all_names:
            print(f'ERROR: unknown step "{n}". Valid: {", ".join(_STEP_NAMES)}')
            sys.exit(1)

    python_exe = sys.executable
    today_str  = datetime.today().strftime('%Y-%m-%d')

    # Deduplicate: pipeline.py appears as both "fx" and "merge"
    # — if both are in the run set, only run pipeline.py once.
    seen_scripts = set()
    total_start = time.perf_counter()
    failed = False

    print(f'\n{"="*50}')
    print(f'  fx_regime pipeline  --  {today_str}')
    print(f'{"="*50}')

    for name, script in STEPS:
        # Filter by --only / --skip
        if args.only is not None and name not in args.only:
            print(f'  [skip]  {name}')
            continue
        if name in args.skip:
            print(f'  [skip]  {name}')
            continue
        # Deduplicate scripts (fx and merge both call pipeline.py)
        if script in seen_scripts:
            print(f'  [dedup] {name}  ({script} already ran)')
            continue
        seen_scripts.add(script)

        print(f'\n>>  {name}  ({script})')
        ok, elapsed = _run_step(name, script, python_exe)
        if ok:
            print(f'OK  {name}  -- {elapsed:.1f}s')
        else:
            print(f'FAIL  {name} after {elapsed:.1f}s')
            print(f'   Fix {script} and re-run:  python run.py --only {name}')
            failed = True
            break

    total = time.perf_counter() - total_start

    if not failed:
        print(f'\n{"="*50}')
        print(f'  all steps done  ({total:.1f}s total)')
        _archive(today_str)
        print()
        print('  live at: https://shreyash3007.github.io/G10-FX-Regime-Detection-Framework/')
        print(f'{"="*50}\n')
    else:
        print(f'\n  pipeline stopped after {total:.1f}s -- fix the error above and retry.\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
