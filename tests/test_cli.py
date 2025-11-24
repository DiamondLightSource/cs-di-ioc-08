import subprocess
import sys

from ebpm_postmortem import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "ebpm_postmortem", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
