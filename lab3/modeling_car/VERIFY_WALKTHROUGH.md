# Problem C Verification Walkthrough (C1-C4)

This walkthrough is a one-by-one checklist to verify a `.pha` model for Problem C.

## 1) Model checklist (before running PHAVerLite)

- Variables:
  - `x`: position (m)
  - `v`: velocity (m/s)
  - Optional `t` for C4 only
- Flows:
  - Accelerate mode uses `x' = v`, `v' = +3.5`
  - Brake mode uses `x' = v`, `v' = -5.5`
  - Stop mode keeps `v = 0`
- Nondeterministic red encounter:
  - Transition into `Brake` allowed for `250 <= x <= 300`
- Initial state:
  - `x = 0`, `v = 0`
- Invariants:
  - Must force leaving `Accel` by `x = 300`
  - Must keep search bounded (e.g., upper bound on `x`)

## 2) Runtime-safe execution rule

Always run with timeout wrappers. Start short, then increase only if needed.

- Quick syntax/sanity: 30-60 s
- Full C3 run: 120-180 s
- C4 timing run: 180 s

Timeout return code (`124`) is treated as inconclusive, not as proof.

## 3) C2 reachable set and figure

1. Run the C3 model to generate reachability outputs.
2. Plot required projection `(x,v)` from generated `out_inv` and `out_reachable`.
3. Save figure for the report.

## 4) C3 property checks

Use `is_reachable` in "bad-state" form, since PHAVerLite is over-approximate:

- If bad state is **unreachable**, the property is proven.
- If bad state is **reachable**, the property is not proven (possible violation or over-approximation artifact).

Required checks:

1. Car cannot cross second intersection (`x >= 500`) with nonzero speed.
2. While braking, speed cannot exceed `46.5 m/s`.
3. While braking, speed cannot exceed `40.0 m/s`.

## 5) C4 timing (ECE622)

Add `t' = 1` and 60 mph target (`26.8 m/s`), then run two bracketing checks:

- Query A: speed `>= 26.8` by time `<= T` (expected unreachable)
- Query B: speed `>= 26.8` by time `<= T+0.1` (expected reachable)

Reported 0-60 time is then in `(T, T+0.1]`.
