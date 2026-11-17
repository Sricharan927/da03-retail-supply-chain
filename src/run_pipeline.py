import subprocess
import sys

STEPS = ["generate_data", "load_db", "run_queries", "forecast", "alerts"]

for name in STEPS:
    print(f"\n--> {name}")
    result = subprocess.run([sys.executable, f"src/{name}.py"])
    if result.returncode != 0:
        sys.exit(f"Step failed: {name}")

print("\nPipeline finished. Start the dashboard with: streamlit run dashboard/app.py")