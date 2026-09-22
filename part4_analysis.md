# Part 4 — Option A: Stop mixing silence

Our implementation is in `tonematrix/optimized.py`. The numbers in this write-up
come from `benchmark_part4.py`, which is just `benchmark.py` with a couple of
extras: it runs the original and our version one after the other on the same
random pattern, repeats each timing and keeps the fastest, and also counts how
many strings are actually ringing (we needed that number for the analysis).

## 1. What we changed

The problem the spec points at is in `ToneMatrix.next_sample` in `matrix.py`:
every single sample, it loops over all `n` strings and calls `next_sample()` on
each one, even if the string has been silent for ages. So at 44100 samples per
second that's `44100 * n` calls per second regardless of what's on the grid.

Instead of copying the whole class we made `optimized.py` subclass the original
`ToneMatrix` and only override the three methods that are about playback:
`next_sample`, `pluck_column` and `resize`. Everything else (`press`, `drag`,
`clear`, `index_of`, `to_text`, the grid layout...) is inherited as-is, which
also means we can't have accidentally changed how editing works.

We added three lists to keep track of which strings are ringing:

| field | what it holds |
|---|---|
| `_ringing` | one `True`/`False` per row: is this string being mixed right now? |
| `_active` | the row numbers that are `True`, kept sorted |
| `_mix` | the actual `StringInstrument` objects for those rows, same order |

How they're used:

* **Waking a string.** In `pluck_column`, after plucking a lit row we call
  `_wake(row)`. If the row wasn't already ringing, it sets the flag, inserts
  the row into `_active` with `bisect.insort` (so it stays sorted) and rebuilds
  `_mix`. If it was already ringing, nothing happens.
* **Mixing.** `next_sample` now loops over `_mix` instead of `self.instruments`.
  That's the whole point: silent strings never get stepped.
* **Retiring a string.** At the start of every column (the `marker == 0`
  branch that already exists for moving the playhead), before plucking the
  next column, we go through `_active` and check each string's `energy()`. If
  it's below `SILENCE_THRESHOLD = 1e-5` the flag is cleared and it's dropped
  from `_active` and `_mix`.
* **Resizing.** `resize` calls the original and then trims or extends the
  three lists. Rows that survived keep ringing, new rows start silent.

The two questions the spec asks about:

**Where does the threshold check go?** Not in the per-sample loop. `energy()`
walks the entire ring buffer, which is up to 401 samples for the 110 Hz bottom
string, so checking every string on every sample would cost way more than the
mixing it's supposed to save. We put it at the column boundary instead, so it
runs once every `S = 8192` samples and its cost is spread out over the whole
column.

**What does "retire" mean if the string gets plucked again?** Retiring just
means "stop calling `next_sample()` on it". We don't clear or reset the buffer.
We didn't need to, because `pluck()` already overwrites the whole buffer with
new noise, so a retired string that gets plucked again is just woken up and
sounds exactly like it would have in the original. The only thing the original
would do differently is keep multiplying those sub-`1e-5` values by 0.995
towards zero, and since one step of 16-bit audio is 1/32767 ≈ 3.05e-5, the
output can't tell the difference anyway. That's also why we picked `1e-5` as
the threshold.

One detail we were careful about: `_mix` is kept in row order so that when every
string is ringing, the floating-point sum happens in the same order as the
original and the output is bit-for-bit identical. We ran the full provided test
harness (87 tests) with `impl.py` pointed at `tonematrix.optimized` and it
passes.

## 2. Running time

Parameters we used:

* `n` — grid size (rows = columns = number of strings)
* `k_c` — number of lit cells in the column being plucked (`0 ≤ k_c ≤ n`)
* `a` — number of strings currently ringing (`0 ≤ a ≤ n`)
* `N` — length of a string's ring buffer, `N = ⌊44100 / f⌋`, at most 401
* `S` — `samples_per_column`, 8192 by default

### Original

A normal call to `next_sample` is **`O(n)`**: the loop `for instrument in
self.instruments` runs exactly `n` times, and each `StringInstrument.next_sample`
is `O(1)` (one dequeue, one peek, one enqueue on the ring buffer, which is
`O(1)` each).

Every `S`-th call also runs `pluck_column`. That scans all `n` rows and calls
`pluck()` on the `k_c` lit ones, and each `pluck()` rotates the whole buffer,
so it's `O(N)`. So a column boundary costs `O(n + k_c·N)`.

Adding it up over one column of `S` samples: **`O(S·n + n + k_c·N)`**, or
per sample `O(n + (n + k_c·N)/S)`. With `S = 8192` and `N ≤ 401` the boundary
part is at most `(n + 401n)/8192`, which is less than `0.05n`, so the original
is basically `Θ(n)` per sample and almost all of the time is in the mixing
loop. This matches what the spec's table shows: µs/sample doubles when `n`
doubles and doesn't really depend on density.

### Optimized

A normal call to `next_sample` is **`O(a)`**: the loop walks `_mix`, which has
exactly the `a` ringing strings in it, and does nothing else. There's no `O(n)`
scan of flags per sample — `_mix` is a real list that only gets rebuilt when
the set of ringing strings changes.

At a column boundary:

* retirement check: `a` calls to `energy()` at `O(N)` each → `O(a·N)`
* rebuilding `_active` and `_mix` if something retired → `O(a)`
* `pluck_column`: the same `O(n)` row scan and `k_c` plucks at `O(N)` each as
  before, plus up to `k_c` wakes. A wake is an `O(a)` `insort` plus an `O(a)`
  rebuild of `_mix`, so worst case `O(k_c·a)`. In practice most plucked rows
  are already ringing and `_wake` returns immediately for those.

Per column: **`O(S·a + a·N + n + k_c·N + k_c·a)`**, so per sample

    O( a + (a·N + n + k_c·N + k_c·a) / S )

With the defaults, `a·N/S` is at most `0.05a`, so the retirement check adds at
most about 5% on top of each ringing string. When we actually measured it, it
was about 1.5% of total time (0.12 s out of 8 s at `n = 32`, 25% density).

So the optimized version is `Θ(a)` per sample where the original is `Θ(n)`,
and the speedup should be roughly `n / a`. Extra memory is three lists of at
most `n` entries, `O(n)`.

## 3. Measurements

Machine: Windows 11, Python 3.11. Command: `benchmark_part4.py --repeat 5`
(fastest of five runs, original and optimized on the same random pattern).
"mean a" is the average number of ringing strings per column in the optimized
run. xRT is seconds of audio per second of real time, so below 1.0 it can't
keep up.

| size n | density | mean a | orig µs/sample | opt µs/sample | speedup | orig xRT | opt xRT |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8  | 0.05 | 0.5  | 5.64  | 0.47  | **12.1x** | 4.02 | 48.75 |
| 8  | 0.25 | 6.1  | 7.11  | 6.52  | 1.09x | 3.19 | 3.48 |
| 8  | 0.50 | 7.1  | 8.24  | 7.95  | 1.04x | 2.75 | 2.85 |
| 8  | 1.00 | 8.0  | 8.83  | 9.28  | **0.95x** | 2.57 | 2.44 |
| 16 | 0.05 | 4.6  | 15.61 | 4.17  | **3.75x** | 1.45 | 5.44 |
| 16 | 0.25 | 14.1 | 14.65 | 13.63 | 1.08x | 1.55 | 1.66 |
| 16 | 0.50 | 15.4 | 15.45 | 14.28 | 1.08x | 1.47 | 1.59 |
| 16 | 1.00 | 16.0 | 15.65 | 15.64 | 1.00x | 1.45 | 1.45 |
| 32 | 0.05 | 17.1 | 30.90 | 16.91 | **1.83x** | 0.73 | 1.34 |
| 32 | 0.25 | 28.4 | 29.82 | 27.63 | 1.08x | 0.76 | 0.82 |
| 32 | 0.50 | 30.6 | 30.75 | 30.90 | 1.00x | 0.74 | 0.73 |
| 32 | 1.00 | 32.0 | 31.22 | 31.17 | 1.00x | 0.73 | 0.73 |

And at size 64 (`--repeat 2` because it takes a while and the laptop was
noisier at this size):

| size n | density | mean a | orig µs/sample | opt µs/sample | speedup | orig xRT | opt xRT |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 0.05 | 33.9 | 63.75 | 25.16 | **2.53x** | 0.36 | 0.90 |
| 64 | 0.25 | 58.9 | 62.29 | 57.72 | 1.08x | 0.36 | 0.39 |
| 64 | 1.00 | 64.0 | 64.36 | 65.06 | 0.99x | 0.35 | 0.35 |

The speedup follows `n / a` pretty closely: 8/0.5 = 16 → 12x, 16/4.6 = 3.5 →
3.75x, 32/17.1 = 1.9 → 1.8x, 64/33.9 = 1.9 → 2.5x. The one we care about most
is `n = 32` at 5% density, where it goes from 0.73x realtime (stutters) to
1.34x (fine).

Something that surprised us: why is `a` so close to `n` even at 25% density?
It's because the strings ring for a really long time. We timed how long a
freshly plucked string takes to drop below `1e-5`:

| row (of 16) | frequency | N | time to retire |
|---|---:|---:|---:|
| 0 (top) | 880 Hz | 50 | 1.4 s |
| 8 | 294 Hz | 150 | 5.4 s |
| 15 (bottom) | 110 Hz | 400 | 15.1 s |

A 16-column loop repeats every `16 · 8192 / 44100 ≈ 3 s`. So except for the
top few rows, any row with at least one lit cell gets re-plucked before it has
decayed, and at 25% density almost every row has at least one lit cell. So
`a → n` and there's nothing left to skip.

## 4. When our version is worse

**Whenever `a ≈ n`, it's a bit slower than the original.** It's doing the same
`n`-way mix plus the retirement checks and list bookkeeping on top. We measured
0.95x at `n = 8` full density and 0.99x at `n = 64`. A fully lit grid is the
obvious case, but as the table above shows it basically also happens at 25%
density on a 16-wide grid because the low strings ring longer than the loop.
So in exactly the situations where the original was already fast enough
(small grids, dense patterns), ours buys nothing and costs a few percent.

**When `samples_per_column` is small, it can be a lot worse.** The `a·N/S`
term stops being negligible. The provided tests actually use
`samples_per_column = 16`, so We measured at `n = 16`, full density, 44100 Hz:

| samples_per_column | orig µs/sample | opt µs/sample |
|---:|---:|---:|
| 16   | 128.1 | 268.1 (**2.1x slower**) |
| 512  | 19.7  | 22.4 (1.14x slower) |
| 8192 | 16.0  | 16.0 |

At `S = 16` the `energy()` walk over every active buffer (`a·N ≈ 16 · 200`
buffer operations) runs every 16 samples and completely dwarfs the mixing it
was supposed to save. The amortisation argument in section 2 only works when
`S` is much bigger than `N`.

**Smaller things:**

* `pluck_column` gets slightly slower. Each *newly* woken row pays an `O(a)`
  insert and an `O(a)` rebuild of `_mix`, so a column that wakes a lot of
  strings at once costs `O(k_c·a)` on top of the original `O(n + k_c·N)`.
  This is still smaller than the `k_c·N` pluck cost as long as `N > a`, but
  it's not free.
* The output is no longer bit-identical once a string has been retired: the
  original would keep adding values below `1e-5` that ours drops. The
  difference is under one 16-bit quantisation step per string and the test
  harness passes, but strictly speaking "behaviour may not change" is only
  true up to that threshold. Lowering the threshold gets closer to the
  original but makes `a` bigger; raising it does the opposite and at some
  point you'd hear notes getting cut off.
* `O(n)` extra memory for the three lists, plus a new list allocation every
  time the active set changes.

Overall: the optimization wins by about `n / a`, which is big exactly when the
pattern is sparse *compared to how long the strings ring*, and it's a small
net loss when it isn't.
