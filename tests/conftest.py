"""Shared pytest fixtures."""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
GEN_CERTS_SCRIPT = REPO_ROOT / "certs" / "gen-certs.sh"


@pytest.fixture(scope="session")
def temp_certs_dir(tmp_path_factory):
    """Generate two unrelated cert sets (trusted and untrusted) in temp directories."""
    good_dir = tmp_path_factory.mktemp("good_certs")
    bad_dir = tmp_path_factory.mktemp("bad_certs")

    for cert_dir in (good_dir, bad_dir):
        subprocess.run(
            [str(GEN_CERTS_SCRIPT), str(cert_dir)],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
        )

    return {"good": good_dir, "bad": bad_dir}
