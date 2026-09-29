# Part 4 Analysis: Option A (Stop Mixing Silence)

For Part 4, we chose **Option A**. The implementation is in `tonematrix/optimized.py`. It keeps the same `ToneMatrix` interface as `tonematrix/matrix.py`, and the only methods that were changed are `__init__`, `next_sample`, and `pluck_column`. Everything else (editing, resizing, and serialization) is the same as in Part 3. The

## 1 and 2. Running Time and Arguments

We use the following parameters:

- `n`: grid size (number of rows, which is also the number of strings)
- `k`: number of lit cells in the column being plucked
- `a`: number of strings in `active_instruments` (ringing strings), where `a <= n`
- `b`: buffer size
- `s`: samples for column = `8192`

**`next_sample()`**
- Original (`matrix.py`): O(n)
- Optimized (`optimized.py`): O(a), since it checks only the list of active instruments with size `a`, and not the entire grid size `n`

**`pluck_column()`**
- Original: O(n + kb) or O(n), since the for loop runs with a size of the grid size `n`, and for every lit cell or `k`, the instrument will be plucked with a size equal to the buffer size `b`.  
- Optimized: O(n + k * (b + a), since the for loop runs with a size of the grid size `n`, and for every lit cell or `k`, the instrument will be plucked with a size equal to the buffer size `b` and a linear check with size `a` or the amount of active instruments will execute for the instrument to be added to the list of active instruments. 

**Retirement check**
- Original: none
- Optimized: O((a * b)/s), since  `energy()` runs a for loop the size of the buffer inside a for loop with size `a` and it is checked only every `8192-1` samples 

## 3. Measurements

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
| 8 | 0.05 | 65536 | 0.028 | 0.432 | 52.53 |
| 8 | 0.25 | 65536 | 0.205 | 3.129 | 7.25 |
| 16 | 0.05 | 131072 | 0.291 | 2.224 | 10.20 |
| 16 | 0.25 | 131072 | 0.703 | 5.366 | 4.23 |
| 32 | 0.05 | 262144 | 1.136 | 4.332 | 5.23 |
| 32 | 0.25 | 262144 | 2.898 | 11.056 | 2.05 |
| 64 | 0.05 | 524288 | 3.967 | 7.567 | 3.00 |
| 64 | 0.25 | 524288 | 10.759 | 20.522 | 1.10 |

## 4. When Our Version Is Worse

Our version performs particularly better in less dense environments or when there is less lit cells but becomes drastically slower when it goes from 0.05 density to 0.25. The original version runs at nearly the same speed at different densities, but slower because it doesn't take into consideration the amount of lit cells and still checks every cell whether it is active or not. Our optimized version exploits the fact that majority of the strings may be silent but it comes at the cost that the length of the list of active instruments `a` is factored into the `pluck_column()` method. The more instruments there is, the longer the linear check of `pluck_column()` will take, and more `energy()` with size `b` which is the buffer size will execute during retirement of strings with O(ab/s) where the retirement will happen ever after samples per column `s`.
