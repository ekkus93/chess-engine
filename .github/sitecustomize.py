import atexit
import runpy
import sys
from pathlib import Path


if Path(sys.argv[0]).name == "task21-5-weighted-search-cleanup.py":
    cleanup = Path(__file__).with_name("task21-5-weighted-search-cleanup2.py")
    atexit.register(lambda: runpy.run_path(str(cleanup), run_name="__main__"))
