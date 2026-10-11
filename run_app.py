"""
CropPricePredict - Helper launcher script
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    app_file = base_dir / "app.py"
    
    print("=" * 60)
    print("🌾 Starting CropPricePredict Application...")
    print(f"📁 Directory: {base_dir}")
    print(f"📄 App File:  {app_file}")
    print("=" * 60)

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_file), "--server.port=8501", "--server.headless=true"]
    subprocess.run(cmd, cwd=str(base_dir))

if __name__ == "__main__":
    main()
