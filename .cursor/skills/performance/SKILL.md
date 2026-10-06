---
name: performance
description: Measurement-driven performance work (BASELINE -> MEASURE -> PROFILE -> CHANGE -> BENCHMARK -> COMPARE) for slow endpoints, queries, loops, builds or memory. Use when the user reports slowness or asks to optimize. Rejects "this should be faster" without evidence.
---

# Performance

"It should be faster" is not evidence. No optimization without a measurement, unless the cause is unambiguous (e.g. an N+1 loop you can read).

## Method

1. **BASELINE**: define the metric (latency p50/p95, throughput, memory, query time), the workload, and the environment. Record current numbers.
2. **MEASURE**: use the project's real tooling (discover it; do not invent): timers/logs, the stack's profiler, `EXPLAIN`/`DBMS_XPLAN` for SQL (with `database`), HTTP timing, build timings. Repeat runs to see variance.
3. **PROFILE**: find where time/memory actually goes (top offenders by measured cost). Label conclusions FACT / INFERENCE / ASSUMPTION.
4. **CHANGE**: one change at a time, targeting the measured bottleneck; prefer the simplest fix (index, batching, caching only if measured to help, removing redundant work).
5. **BENCHMARK**: same workload and environment as the baseline.
6. **COMPARE**: report before/after with numbers; if the gain is within noise or the correctness tests fail, revert the change.

Never trade away correctness, security or necessary observability for speed. Do not add caches/infra without a measured need.

## Output

```
# PERFORMANCE REPORT
Metric & workload / Baseline / Profile findings (top N) / Change / After / Delta / Correctness (tests) / Next bottleneck or "enough"
```

If measurement is impossible in this environment, say what is needed (data, access, tool) instead of guessing.
