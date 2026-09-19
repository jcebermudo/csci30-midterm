"""Part 3: the tone matrix.

A grid_size x grid_size grid of cells, stored as a *flat* list in row-major
order, plus one StringInstrument per row.

Rules for this file:
  * self.grid is a flat list of bools of length grid_size ** 2. Do not use a
    list of lists, a dict, a set, or numpy.
  * The list is fixed-length: no append/pop/insert/remove. resize() is the
    one place you build a new list, and even there you copy element by
    element.
"""

from tonematrix.audio import SAMPLE_RATE, SAMPLES_PER_COLUMN
from tonematrix.scales import frequency_for_row
from tonematrix.string_instrument import StringInstrument

ON = "#"
OFF = "."


class ToneMatrix:
    def __init__(self, grid_size, sample_rate=SAMPLE_RATE,
                 samples_per_column=SAMPLES_PER_COLUMN):
        """Build an all-off grid_size x grid_size matrix.

        Set up:
          * self.grid          - flat list of grid_size ** 2 False values
          * self.instruments   - one StringInstrument per row, tuned with
                                  frequency_for_row(row, grid_size)
          * self.column        - the column the playhead is about to pluck
          * whatever bookkeeping you need for next_sample() and drag()

        Raise ValueError if grid_size < 1.
        """
        # TODO (Milestone 5)
        raise NotImplementedError("ToneMatrix.__init__")

    ### indexing

    def index_of(self, row, col):
        """Map a (row, col) pair to its index in the flat list.

        Raise IndexError if the position is off the grid.
        """
        # TODO (Milestone 5)
        raise NotImplementedError("ToneMatrix.index_of")

    def is_on(self, row, col):
        """Provided, once index_of works."""
        return self.grid[self.index_of(row, col)]

    def set_cell(self, row, col, value):
        """Provided, once index_of works."""
        self.grid[self.index_of(row, col)] = bool(value)

    ### editing

    def press(self, row, col):
        """The user clicked this cell: toggle it.

        Also remember what the cell became, so that drag() can copy it.
        """
        # TODO (Milestone 6)
        raise NotImplementedError("ToneMatrix.press")

    def drag(self, row, col):
        """The user dragged across this cell after a press().

        The cell takes on the same value the pressed cell ended up with: a
        drag that started by switching a cell on paints cells on, and a drag
        that started by switching one off erases.
        """
        # TODO (Milestone 6)
        raise NotImplementedError("ToneMatrix.drag")

    def clear(self):
        """Switch every cell off, without replacing the list."""
        # TODO (Milestone 6)
        raise NotImplementedError("ToneMatrix.clear")

    ### playback

    def next_sample(self):
        """Return the next sample of audio, advancing time by one step.

        On the very first call, and on every samples_per_column-th call after
        that: pluck every lit cell in the current column, then move the
        playhead one column right, wrapping around.

        Every call, including those ones, returns the sum of next_sample()
        over all the instruments.
        """
        # TODO (Milestone 7)
        raise NotImplementedError("ToneMatrix.next_sample")

    def pluck_column(self, col):
        """Pluck the string of every lit row in this column."""
        # TODO (Milestone 7)
        raise NotImplementedError("ToneMatrix.pluck_column")

    ### resizing

    def resize(self, new_size):
        """Change the grid to new_size x new_size.

        Cells present in both the old and new grid keep their values; new
        cells start off. Instruments for rows that survive are reused as-is,
        rows beyond the old size get fresh instruments. The playhead resets
        to column 0 and the next call to next_sample() plucks immediately.

        Raise ValueError if new_size < 1.
        """
        # TODO (Milestone 8)
        raise NotImplementedError("ToneMatrix.resize")

    ### serialization

    def to_text(self):
        """Render the grid as grid_size lines of '#' and '.'."""
        # TODO (Milestone 6)
        raise NotImplementedError("ToneMatrix.to_text")

    @classmethod
    def from_text(cls, text, **kwargs):
        """Build a matrix from the format to_text() produces. Provided."""
        rows = [line.strip() for line in text.strip().splitlines() if line.strip()]
        size = len(rows)
        if any(len(line) != size for line in rows):
            raise ValueError("pattern must be square")

        matrix = cls(size, **kwargs)
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                matrix.set_cell(r, c, ch == ON)
        return matrix

    def __str__(self):
        return self.to_text()
