from pathlib import Path
import sys

def resource_path(*parts):
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent

    return base.joinpath(*parts)
