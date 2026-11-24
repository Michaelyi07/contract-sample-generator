import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(REPO_ROOT, "samples")


@pytest.fixture(scope="session")
def samples_dir() -> str:
    if not os.path.isdir(SAMPLES_DIR):
        pytest.skip("default samples/ not generated; run: python gen_fake_contracts.py --seed 42")
    return SAMPLES_DIR
