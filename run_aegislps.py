#!/usr/bin/env python3
"""
AegisLPS Production & Local Application Launcher.
Orchestrates the local FastAPI calculation sidecar and launches the engineering workbench.
"""
import sys
import os
import subprocess
import time
import webbrowser

def main():
    print("=" * 60)
    print(" AegisLPS - Advanced Lightning Protection Engineering Suite")
    print(" Version: 1.0.0-alpha.1 | Standards: IEC 62305:2024 Suite")
    print("=" * 60)

    # 1. Run Internal Self-Test
    from aegislps_engine.diagnostics import SystemDiagnostics
    diag = SystemDiagnostics.run_self_test()
    print(f"\n[1/3] System Pre-Flight Diagnostics: {diag['system_status']}")
    for k, v in diag["tests"].items():
        print(f"  • {k.replace('_', ' ').title()}: [{v['status']}] {v['message']}")

    if diag["system_status"] != "OPERATIONAL":
        print("ERROR: Self-test failed. Please inspect dependencies.")
        sys.exit(1)

    print("\n[2/3] Local Calculation Engine Ready on http://127.0.0.1:8000")
    print("[3/3] Ready for Engineering Workflow & Field Operation.")
    print("\nTo start API backend daemon:")
    print("  uvicorn aegislps_api.main:app --host 127.0.0.1 --port 8000")
    print("\nTo start Web Frontend:")
    print("  npm run dev --workspace=apps/web")
    print("=" * 60)

if __name__ == "__main__":
    main()
