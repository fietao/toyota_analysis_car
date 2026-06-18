import os
import time
import subprocess
import shutil
import sys
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("watchdog is not installed. Please run: pip install watchdog")
    sys.exit(1)

BASE = Path(__file__).resolve().parent
INPUT_DIR = BASE / "input"
OUTPUT_DIR = BASE / "output"
RAW_DIR = BASE / "raw data"
PIPELINE_SCRIPT = BASE / ".claude" / "scripts" / "run_pipeline.py"

# Ensure directories exist
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)

class ExcelHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        if filepath.suffix == '.xlsx' and not filepath.name.startswith("~"):
            print(f"\n[Watcher] New file detected: {filepath.name}")
            # Wait for file to finish copying
            time.sleep(2)
            
            # Move the file to raw data directory
            try:
                dest = RAW_DIR / filepath.name
                shutil.move(str(filepath), str(dest))
                print(f"[Watcher] Moved to raw data folder.")
                
                # Run the pipeline
                print(f"[Watcher] Triggering pipeline...")
                result = subprocess.run(
                    [sys.executable, str(PIPELINE_SCRIPT)],
                    cwd=str(BASE),
                    env={**os.environ, "PYTHONUTF8": "1"}
                )
                
                if result.returncode == 0:
                    print(f"[Watcher] Pipeline completed successfully!")
                    
                    # Move the generated analyst report to output directory
                    for f in BASE.glob("*(test analyst).xlsx"):
                        shutil.move(str(f), str(OUTPUT_DIR / f.name))
                        print(f"[Watcher] Moved report to {OUTPUT_DIR.name}/{f.name}")
                        
                    # Here we would trigger JSON export for Next.js dashboard
                    export_dashboard_data()
                else:
                    print(f"[Watcher] Pipeline failed with code {result.returncode}")
            
            except Exception as e:
                print(f"[Watcher] Error processing file: {e}")

def export_dashboard_data():
    """Extract pivot tables from the generated report into JSON for the web dashboard."""
    print("[Watcher] Exporting JSON data for the dashboard...")
    result = subprocess.run(
        [sys.executable, "export_dashboard.py"],
        cwd=str(BASE),
        env={**os.environ, "PYTHONUTF8": "1"}
    )
    if result.returncode == 0:
        print("[Watcher] JSON export successful.")
    else:
        print("[Watcher] JSON export failed.")

def start_watcher():
    print(f"Monitoring '{INPUT_DIR.name}/' directory for new Excel files...")
    event_handler = ExcelHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INPUT_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()
