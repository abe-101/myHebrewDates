import shutil
import subprocess
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parents[1] / "static" / "js"
NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None, reason="needs Node.js")
@pytest.mark.parametrize("script", sorted(JS_DIR.glob("*.js")), ids=lambda p: p.name)
def test_script_parses(script):
    # Production bundles these files into one, so one syntax error breaks them all.
    result = subprocess.run(  # noqa: S603
        [str(NODE), "--check", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
