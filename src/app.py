"""PhasorQ web entry point. Run: streamlit run src/app.py"""

from pathlib import Path
import runpy
import sys

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Streamlit reruns this entry point after each interaction.
runpy.run_module("src.ui", run_name="__main__")
