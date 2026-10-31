import subprocess
import sys
import os
import glob
import tempfile
import pytest

def test_internal_packages_wheel_build_and_metadata():
    """
    PKG-004 / PKG-005: Clean wheel build test
    Verifies that all 6 internal packages can build valid wheels with PEP 440 versions.
    """
    packages = [
        "packages/standards-data",
        "packages/domain-model",
        "packages/geometry",
        "packages/reporting",
        "services/calculation-engine",
        "services/api"
    ]

    with tempfile.TemporaryDirectory() as dist_dir:
        for pkg_path in packages:
            cmd = [
                sys.executable, "-m", "pip", "wheel",
                "--no-deps",
                "-w", dist_dir,
                pkg_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            assert res.returncode == 0, f"Failed to build wheel for {pkg_path}: {res.stderr}"

        wheels = glob.glob(os.path.join(dist_dir, "*.whl"))
        assert len(wheels) == 6, f"Expected 6 wheels, found {len(wheels)}: {wheels}"
        for w in wheels:
            assert "1.0.0a1" in os.path.basename(w)
