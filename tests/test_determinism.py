"""AC-1: two runs with the same random seed produce identical sha256 hashes."""

import hashlib
import os

from contract_gen.generator import generate


def _tree_hashes(root: str) -> dict[str, str]:
    out = {}
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root)
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            out[rel] = h.hexdigest()
    return out


def test_same_seed_produces_identical_sha256(tmp_path):
    """Full default run (4 layouts x 10 = 40 docs, incl. rasterized scan/photo
    PDFs) executed twice; every PDF and ground_truth file must hash equal."""
    run1 = str(tmp_path / "run1")
    run2 = str(tmp_path / "run2")
    generate(seed=42, per_layout=10, out_dir=run1, verbose=False)
    generate(seed=42, per_layout=10, out_dir=run2, verbose=False)
    h1 = _tree_hashes(run1)
    h2 = _tree_hashes(run2)
    assert len(h1) == 80  # 40 PDFs + 40 ground_truth.json
    assert h1 == h2


def test_different_seed_produces_different_bytes(tmp_path):
    run_a = str(tmp_path / "a")
    run_b = str(tmp_path / "b")
    generate(seed=42, per_layout=1, out_dir=run_a, verbose=False)
    generate(seed=43, per_layout=1, out_dir=run_b, verbose=False)
    h_a = _tree_hashes(run_a)
    h_b = _tree_hashes(run_b)
    assert h_a.keys() == h_b.keys()
    assert h_a != h_b  # seeds matter: not a constant corpus
