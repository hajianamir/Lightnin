# Characterization Baseline Snapshots

These snapshots capture the numerical outputs of the calculation and geometry
engines for fixed reference inputs and deterministic random seeds, with one JSON
file per engine under `tests/characterization/baseline/`.

- **Purpose:** Detect any unintended or intended numerical change across steps.
- **Current behaviour only:** These snapshots are a regression baseline, NOT a
  standards or mathematical validation. They record what the engines output
  right now, including known defects.
- **Regeneration:** Run:

  ```bash
  python tests/characterization/generate_baseline.py
  ```

  Regenerate snapshots **only** in a step whose instructions explicitly allow
  updating the characterization baseline.
