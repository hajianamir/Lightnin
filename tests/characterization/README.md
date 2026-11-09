# Characterization snapshots

These files record the **current** numerical output of the calculation engines for
fixed inputs (`generate_baseline.py`). They are a regression guard, not a validation.

- Some recorded values are known to be **wrong** (see the supervisor review: rolling-sphere
  geometry, touch/step, Heidler parameters, ring-electrode l1 rule, K_MS, separation kc).
  The snapshot preserves that behaviour on purpose so that every later change is visible.
- A failing test means behaviour changed. That is not automatically a bug; review the diff first.
- Regenerate only in a step that explicitly allows it:

      python tests/characterization/generate_baseline.py

- Generation is deterministic (fixed seeds, sorted keys, 9 significant digits).
