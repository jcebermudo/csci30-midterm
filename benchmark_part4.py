"""Extension of benchmark.py for the Part 4 write-up (Option A).

    python benchmark_part4.py
    python benchmark_part4.py --sizes 8 16 32 --densities 0.05 0.25 1.0 --repeat 3

Differences from benchmark.py:
  * runs the original and the optimized ToneMatrix back to back on the same
    pattern, so machine noise hits both equally;
  * repeats each measurement and keeps the fastest run;
  * reports `a`, the mean number of ringing strings per column for the
    optimized version, which is the parameter its running time depends on.
"""

import argparse
import time

from benchmark import fill, load
from tonematrix.audio import SAMPLES_PER_COLUMN


def time_one_pass(ToneMatrix, size, density, repeat):
    best = float("inf")
    active = None
    for _ in range(repeat):
        matrix = ToneMatrix(size)
        fill(matrix, density)
        total = size * SAMPLES_PER_COLUMN
        counts = []
        start = time.perf_counter()
        for _ in range(total):
            matrix.next_sample()
            if matrix.marker == 1 and hasattr(matrix, "_active"):
                counts.append(len(matrix._active))
        elapsed = time.perf_counter() - start
        best = min(best, elapsed)
        if counts:
            active = sum(counts) / len(counts)
    return best, active


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 16, 32, 64])
    parser.add_argument("--densities", type=float, nargs="+",
                        default=[0.05, 0.25, 1.0])
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()

    Original = load("matrix")
    Optimized = load("optimized")

    print(f"{'size':>5} {'density':>8} {'mean a':>7} | "
          f"{'orig us/smp':>12} {'opt us/smp':>11} {'speedup':>8} | "
          f"{'orig xRT':>9} {'opt xRT':>8}")
    for size in args.sizes:
        for density in args.densities:
            total = size * SAMPLES_PER_COLUMN
            audio = total / 44100
            t_orig, _ = time_one_pass(Original, size, density, args.repeat)
            t_opt, a = time_one_pass(Optimized, size, density, args.repeat)
            print(f"{size:>5} {density:>8.2f} {a:>7.1f} | "
                  f"{1e6 * t_orig / total:>12.3f} {1e6 * t_opt / total:>11.3f} "
                  f"{t_orig / t_opt:>7.2f}x | "
                  f"{audio / t_orig:>9.2f} {audio / t_opt:>8.2f}", flush=True)


if __name__ == "__main__":
    main()
