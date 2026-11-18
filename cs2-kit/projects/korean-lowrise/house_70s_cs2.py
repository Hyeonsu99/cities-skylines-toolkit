"""70년대 기와 양옥 대표."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from house_core import PRESETS, build_and_export

if __name__ == "__main__":
    build_and_export(PRESETS["70s"])
