"""Part 4, Option A: stop mixing silence.

The original ToneMatrix.next_sample calls next_sample on every one of the
n strings for every one of the 44100 samples in a second, even though most
strings are silent most of the time. This version keeps track of which
strings are actually ringing, mixes only those, and retires a string once
its energy has fallen below anything the 16-bit output could reproduce.

Only playback changes (next_sample, pluck_column, resize). Everything else
is inherited from tonematrix.matrix.ToneMatrix unchanged, so the grid is
still the same flat list and editing still behaves identically.

Bookkeeping added on top of the base class:
  * self._ringing  - one bool per row: is that string currently being mixed?
  * self._active   - the rows whose flag is True, kept in ascending order so
                     the mix is summed in the same row order as the original.
  * self._mix      - the StringInstrument objects for those rows, in the same
                     order. This is what the per-sample loop walks, so that
                     loop does no indexing at all. It is rebuilt only when
                     the active set changes (a pluck, a retirement, a resize).
"""

from bisect import insort

from tonematrix.matrix import ToneMatrix as _BaseToneMatrix

# A string whose mean absolute displacement is below this is retired. One
# step of 16-bit audio is 1/32767 = 3.05e-5, so a string this quiet cannot
# move the output by even a single quantisation level on its own.
SILENCE_THRESHOLD = 1e-5


class ToneMatrix(_BaseToneMatrix):
    def __init__(self, grid_size, *args, **kwargs):
        super().__init__(grid_size, *args, **kwargs)
        self._ringing = [False] * grid_size
        self._active = []
        self._mix = []

    ### playback

    def _rebuild_mix(self):
        self._mix = [self.instruments[row] for row in self._active]

    def _wake(self, row):
        """Mark a string as ringing so that next_sample mixes it."""
        if not self._ringing[row]:
            self._ringing[row] = True
            insort(self._active, row)
            self._rebuild_mix()

    def _retire_quiet_strings(self):
        """Drop every active string whose energy has decayed to silence.

        Costs O(a * N) where a is the number of ringing strings and N the
        buffer length, so it is only ever called at a column boundary, not
        on every sample.
        """
        retired = False
        for row in self._active:
            if self.instruments[row].energy() < SILENCE_THRESHOLD:
                self._ringing[row] = False
                retired = True
        if retired:
            self._active = [row for row in self._active if self._ringing[row]]
            self._rebuild_mix()

    def next_sample(self):
        result = 0
        if self.marker == 0:
            self._retire_quiet_strings()
            self.pluck_column(self.column)
            self.column = (self.column + 1) % self.grid_size
        for instrument in self._mix:
            result += instrument.next_sample()
        self.marker = (self.marker + 1) % self.samples_per_column
        return result

    def pluck_column(self, col):
        if col > len(self.grid)**0.5-1:
            raise IndexError("column out of bounds")

        for i in range(len(self.instruments)):
            if self.grid[self.index_of(i, col)]:
                self.instruments[i].pluck()
                self._wake(i)

    ### resizing

    def resize(self, new_size):
        super().resize(new_size)
        # Rows that survived keep ringing; rows beyond the old size are fresh
        # (silent) instruments, so they start out retired.
        del self._ringing[new_size:]
        self._ringing.extend([False] * (new_size - len(self._ringing)))
        self._active = [row for row in self._active if row < new_size]
        self._rebuild_mix()
