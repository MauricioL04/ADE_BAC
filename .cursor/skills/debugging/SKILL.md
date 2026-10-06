---
name: debugging
description: Root cause analysis for bugs, failing tests, errors and unexpected behavior (SYMPTOM -> REPRODUCE -> TRACE -> ISOLATE -> ROOT CAUSE -> FIX -> REGRESSION TEST). Use before changing code to fix anything whose cause is not already proven.
---

# Debugging

No random edits until the error goes away. Every change must follow from an established cause.

## Method (do not skip steps)

1. **SYMPTOM**: exact error/behavior, expected vs actual, where/when. Quote logs/stack traces (mask secrets).
2. **REPRODUCE**: a command or minimal test that fails deterministically. If you cannot reproduce, say so and collect more evidence; do not guess a fix.
3. **TRACE**: follow the real flow from input to failure; read the code, do not assume. Check recent changes (`git log -p` on the area) and every caller of the suspect function.
4. **ISOLATE**: bisect (inputs, commits, components) until the smallest failing case remains.
5. **ROOT CAUSE**: state it as a FACT with evidence (file:line, value observed). Distinguish cause from trigger.
6. **FIX**: the smallest change at the shared point of failure (fix once where all callers route through), not per-symptom patches.
7. **REGRESSION TEST**: the reproduction from step 2 becomes a test that fails before the fix and passes after. Then run the full validation (`python scripts/ade/verify.py`).

## Output

```
# ROOT CAUSE ANALYSIS
Symptom / Reproduction (command) / Trace / Isolation / Root cause (FACT + evidence)
Fix (files) / Regression test / Other callers checked / Residual risk
```

Two failed hypotheses in a row: stop, re-read the trace, and report what is known instead of trying a third guess blindly.
