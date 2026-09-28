# Part 4 Analysis: Option A (Stop Mixing Silence)

For Part 4, we chose **Option A**. The implementation is in `tonematrix/optimized.py`. It keeps the same `ToneMatrix` interface as `tonematrix/matrix.py`, and the only methods that were changed are `__init__`, `next_sample`, and `pluck_column`. Everything else (editing, resizing, and serialization) is the same as in Part 3.

## 1. Running Time

We use the following parameters:

- `n`: grid size (number of rows, which is also the number of strings)
- `k_c`: number of lit cells in the column being plucked
- `a`: number of strings in `active_instruments` (ringing strings), where `a <= n`
- `L`: buffer length of a string, which is `44100 // frequency`. Since the lowest note is 110 Hz, `L <= 400`.
- `S`: samples per column, `SAMPLES_PER_COLUMN = 8192`

**`next_sample`, mixing (every call)**
- Original (`matrix.py`): O(n)
- Optimized (`optimized.py`): O(a)

**`pluck_column` (once per column)**
- Original: O(n + k_c · L)
- Optimized: O(n + k_c · (L + a))

**Retirement check (once per column)**
- Original: none
- Optimized: O(a · L)

**`next_sample`, amortized per sample**
- Original: O(n + (n + k_c · L) / S) = O(n)
- Optimized: O(a + (n + k_c · (L + a) + a · L) / S) = O(a)

**One full pass of the playhead (`n · S` samples)**
- Original: O(n² · S)
- Optimized: O(a_avg · n · S), where `a_avg` is the average of `a` over the pass

## 2. Arguments for Each Bound

**Original mixing: O(n).** The loop visits every string, and there is one string per row, so it runs `n` times. Each iteration is O(1).

**Optimized mixing: O(a).** The loop visits only the active strings, so it runs `a` times. Each iteration is O(1). A string is never added twice, so `a <= n`.

**Original `pluck_column`: O(n + k_c · L).** The loop checks every row, so it runs `n` times. Only the `k_c` lit rows are plucked, and each pluck rewrites all `L` buffer samples.

**Optimized `pluck_column`: O(n + k_c · (L + a)).** Same loop as the original, but each of the `k_c` lit rows also scans the active list (length `a`) to avoid adding a duplicate.

**Retirement check: O(a · L).** The loop runs once per active string, so `a` times. Each energy check reads all `L` buffer samples.

**Amortized per sample.** The per-column work runs once every `S = 8192` samples, and `S` is much larger than `n` and `L`, so spreading it over `S` samples does not change the bound. The mixing loop dominates.

**Full pass.** A pass is `n` columns of `S` samples, so `n · S` calls at O(n) or O(a) each.

## 3. Measurements

Both versions were measured with the provided `benchmark.py`, unchanged, on the same machine:

```
python benchmark.py
python benchmark.py --impl optimized
```

Each row is one full pass of the playhead (`n · 8192` samples). "x realtime" is seconds of audio produced per second of running time. Below 1.0 means the sequencer cannot keep up with playback.

**Before: original (`python benchmark.py`)**

| size | density | samples | seconds | μs/sample | x realtime |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.05 | 65536 | 0.437 | 6.663 | 3.40 |
| 8 | 0.25 | 65536 | 0.431 | 6.581 | 3.45 |
| 16 | 0.05 | 131072 | 1.675 | 12.779 | 1.77 |
| 16 | 0.25 | 131072 | 2.592 | 19.778 | 1.15 |
| 32 | 0.05 | 262144 | 11.676 | 44.540 | 0.51 |
| 32 | 0.25 | 262144 | 11.471 | 43.757 | 0.52 |
| 64 | 0.05 | 524288 | 44.611 | 85.089 | 0.27 |
| 64 | 0.25 | 524288 | 43.090 | 82.188 | 0.28 |

**After: optimized (`python benchmark.py --impl optimized`)**

| size | density | samples | seconds | μs/sample | x realtime |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.05 | 65536 | 0.037 | 0.563 | 40.25 |
| 8 | 0.25 | 65536 | 0.355 | 5.411 | 4.19 |
| 16 | 0.05 | 131072 | 0.494 | 3.770 | 6.02 |
| 16 | 0.25 | 131072 | 1.384 | 10.560 | 2.15 |
| 32 | 0.05 | 262144 | 3.354 | 12.796 | 1.77 |
| 32 | 0.25 | 262144 | 10.034 | 38.278 | 0.59 |
| 64 | 0.05 | 524288 | 13.130 | 25.043 | 0.91 |
| 64 | 0.25 | 524288 | 33.683 | 64.245 | 0.35 |


## 4. When Our Version Is Worse

**Dense patterns.** When most strings are always ringing, `a` is close to `n`, so mixing costs the same as the original. On top of that, our version does extra work: the retirement check calls `energy()` on every active string once per column, and `pluck_column` checks the active list before adding a string. The benchmark shows this: the speedup falls from about 3.4x at density `0.05` to as low as 1.14x at `0.25` (size 32).

**The output is not exactly the same.** A string is retired once its energy drops below `0.01`, but it is not completely silent yet. The original keeps mixing that quiet leftover sound, while our version drops it.

**Checking only once per column.** Retirement is checked only every 8192 samples, so a string that has gone quiet can still be mixed for up to one more column (about 0.19 seconds) before it is removed.
