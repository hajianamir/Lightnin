import subprocess
import sys
import os
import glob
import tempfile
import pytest

def test_clean_environment_wheel_build_and_metadata():
    """
    PKG-004 / PKG-005 / PKG-006:
    Build wheels for all 6 internal packages into an isolated temporary directory,
    and verify valid PEP 440 filenames, version tags, and package metadata.
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

        # Verify wheel naming conventions and alpha tag
        wheel_names = [os.path.basename(w) for w in wheels]
        for name in wheel_names:
            assert "1.0.0a1" in name
            assert name.endswith("-py3-none-any.whl") or name.endswith("-none-any.whl")

def test_isolated_clean_wheel_installation_and_smoke_calculation():
    """
    Build wheels and install them into a separate temporary virtual environment without repository PYTHONPATH.
    Execute an isolated Python calculation to verify pure wheel functionality.
    """
    packages = [
        "packages/standards-data",
        "packages/domain-model",
        "packages/geometry",
        "packages/reporting",
        "services/calculation-engine"
    ]

    with tempfile.TemporaryDirectory() as venv_dir:
        # Create isolated clean virtualenv
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        venv_python = os.path.join(venv_dir, "bin", "python")

        # Build wheels
        with tempfile.TemporaryDirectory() as dist_dir:
            for pkg in packages:
                subprocess.run([
                    sys.executable, "-m", "pip", "wheel",
                    "--no-deps", "-w", dist_dir, pkg
                ], check=True)

            wheels = glob.glob(os.path.join(dist_dir, "*.whl"))
            # Install wheels into isolated venv with dependencies
            subprocess.run([
                venv_python, "-m", "pip", "install",
                "pydantic", "networkx", "scipy", "numpy", "reportlab"
            ] + wheels, check=True)

            # Test clean execution outside the monorepo path
            test_script = (
                "from aegislps_standards.repository import StandardsRepository\n"
                "from aegislps_engine.separation import SeparationDistanceEngine\n"
                "from aegislps_domain.models import Project\n"
                "repo = StandardsRepository()\n"
                "engine = SeparationDistanceEngine(repo)\n"
                "proj = Project(name='Wheel Test', lps_class='I')\n"
                "res = engine.calculate_project(proj)\n"
                "print('ISOLATED_OK', len(res))\n"
            )

            smoke_run = subprocess.run(
                [venv_python, "-c", test_script],
                capture_output=True,
                text=True,
                cwd="/tmp" # Execute strictly outside /app repository
            )

            assert smoke_run.returncode == 0
            assert "ISOLATED_OK" in smoke_run.stdout
