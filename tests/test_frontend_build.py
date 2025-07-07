import pytest
import subprocess
from pathlib import Path
import shutil


def test_frontend_build():
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    npm = shutil.which("npm")
    if npm is None:
        pytest.skip("npm not installed")
    subprocess.run([npm, "ci", "--no-audit", "--no-fund"], cwd=frontend, check=True)
    subprocess.run([npm, "run", "build"], cwd=frontend, check=True)


