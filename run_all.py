# run_all.py
import subprocess
import sys

print("running full pipeline...\n")
subprocess.run([sys.executable, "pipeline.py"],        check=True)
subprocess.run([sys.executable, "cot_pipeline.py"],    check=True)
subprocess.run([sys.executable, "create_dashboards.py"], check=True)
print("\ndone. check /charts for today's dashboards.")

