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
from array import array

ON = "#"
OFF = "."


class ToneMatrix:
    def __init__(self, grid_size, sample_rate=SAMPLE_RATE,
                 samples_per_column=SAMPLES_PER_COLUMN):
        if grid_size < 1:
            raise ValueError("Grid size too small")

        self.grid_size = grid_size
        self.grid = [False]*grid_size**2
        self.instruments = []
        for i in range(grid_size):
            self.instruments.append(StringInstrument(frequency_for_row(i, grid_size), sample_rate))
        self.column = 0
        self.state = False
        self.marker = 0
        self.sample_state = (self.marker+ 1) % samples_per_column 

    def index_of(self, row, col):
        if row < 0 or row >= (self.grid_size):
            raise IndexError ("Position off-grid")

        if col < 0 or col >= (self.grid_size):
            raise IndexError("Position off-grid")
        
        return (self.grid_size*row) + col

    def is_on(self, row, col):
        return self.grid[self.index_of(row, col)]

    def set_cell(self, row, col, value):
        self.grid[self.index_of(row, col)] = bool(value)

    def press(self, row, col):
        if self.grid[self.index_of(row, col)]:
            self.grid[self.index_of(row, col)] = False
            self.state = False
        else:
            self.grid[self.index_of(row, col)] = True
            self.state = True
         
     
    def drag(self, row, col):
        while not self.state:
            self.grid[self.index_of(row, col)] = False

        while self.state:
            self.grid[self.index_of(row, col)] = True

    def clear(self):
        for i in(len(self.grid)):
            if self.grid[i]:
                self.grid[i] = False

    ### playback

    def next_sample(self):

        result = 0
        if self.marker == 0:
            self.pluck_column(self.column)
        for i in range(len(self.instruments)):
            if self.grid[self.index_of(i,self.column)]:
                result += self.instruments[1].next_sample()
        self.marker += 1
        return result

    def pluck_column(self, col):
        if col > len(self.grid)**0.5-1:
            raise IndexError("column out of bounds")
        
        for i in range(len(self.instruments)):
            if self.grid[self.index_of(i,col)]:
                self.instruments[1].pluck()

    ### resizing

    def resize(self, new_size):
        if new_size < 1:
            raise ValueError("Grid size too small")
    
        old_size = self.grid_size
        old_grid = self.grid
   
        self.grid = array("b", [False] * (new_size ** 2))

        if old_size > new_size:
            overlap = new_size
        else: 
            overlap = old_size
    
        for row in range(overlap):
            for column in range(overlap):
                old_index = row * old_size + column
                new_index = row * new_size + column
                self.grid[new_index] = old_grid[old_index]
    
  
        if new_size > old_size:
            for row in range(old_size, new_size):
                self.instruments.append(StringInstrument(frequency_for_row(row, new_size)))
        else:
            self.instruments = self.instruments[:new_size]
    
        self.grid_size = new_size
        self.column = 0
        self.samples_since_pluck = 0
        
        raise NotImplementedError("ToneMatrix.resize")

    ### serialization

    def to_text(self):
        result = ""
        for i in(len(self.grid)):
            if i:
                result += "#"
            else:
                result += "."
        return result

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
