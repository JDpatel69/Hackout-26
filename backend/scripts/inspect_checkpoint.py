"""
Inspect the image segmentation checkpoint (best.pt) to recover the exact
preprocessing constants the ONNX export does not carry.

The ONNX file (algae_segmentation.onnx) stores only the graph — not the
normalization mean/std or the training tile size. Those live in the PyTorch
checkpoint. Run this ONCE in the torch-enabled training environment
(Models/.venv, created by Models/setup_env.ps1) and paste the printed values
into backend/.env:

    AI_IMAGE_TILE_SIZE=<size>
    AI_IMAGE_NORM_MEAN=<m0,m1,m2>
    AI_IMAGE_NORM_STD=<s0,s1,s2>

Usage (from the Models torch env):
    python inspect_checkpoint.py "C:\\Users\\dharm\\OneDrive\\Desktop\\Models\\best.pt"

Note: the backend defaults to ImageNet stats, which empirically discriminate
algae (green) vs. open water (blue) decisively — so this step is a refinement,
not a blocker.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    ckpt_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("best.pt")
    if not ckpt_path.exists():
        print(f"Checkpoint not found: {ckpt_path}")
        return 1

    try:
        import torch
    except ImportError:
        print("torch is not installed in this environment. Run inside the Models training env.")
        return 2

    ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    if not isinstance(ckpt, dict):
        print(f"Loaded object is a {type(ckpt).__name__}, not a dict of metadata.")
        return 0

    keys_of_interest = ["arch", "encoder", "size", "norm_mean", "norm_std", "num_classes"]
    print("=== checkpoint metadata ===")
    for k in keys_of_interest:
        if k in ckpt:
            print(f"  {k:12s} = {ckpt[k]}")
    print("\n=== all top-level keys ===")
    print("  " + ", ".join(sorted(str(k) for k in ckpt.keys())))

    mean = ckpt.get("norm_mean")
    std = ckpt.get("norm_std")
    size = ckpt.get("size")
    if mean is not None and std is not None:
        print("\n=== paste into backend/.env ===")
        if size:
            print(f"AI_IMAGE_TILE_SIZE={int(size) if not isinstance(size, (list, tuple)) else size[0]}")
        print("AI_IMAGE_NORM_MEAN=" + ",".join(str(round(float(x), 6)) for x in mean))
        print("AI_IMAGE_NORM_STD=" + ",".join(str(round(float(x), 6)) for x in std))
    else:
        print("\nNo norm_mean/norm_std in checkpoint; ImageNet defaults in backend/.env are appropriate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
