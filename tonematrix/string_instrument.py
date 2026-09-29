from tonematrix.audio import SAMPLE_RATE
from tonematrix.ring_buffer import RingBuffer

# Height of the square wave written into the buffer by pluck().
PLUCK_AMPLITUDE = 0.05

# How much of its energy the string keeps on each trip around the buffer.
DECAY = 0.995


class StringInstrument:

    def __init__(self, frequency, sample_rate=SAMPLE_RATE):
        if frequency <= 0:
            raise ValueError("Frequency too little") 

        if sample_rate//frequency < 2:
            raise ValueError("Too little samples")

        self.frequency = frequency
        self.capacity = int(sample_rate//frequency)
        self.buffer = RingBuffer(self.capacity)
        for i in range(self.capacity):
            self.buffer.enqueue(0.0)

    @classmethod
    def make_from_array(cls, values, frequency=None, sample_rate=SAMPLE_RATE):
        string = cls.__new__(cls)
        string.frequency = (frequency if frequency is not None
                            else sample_rate / len(values))
        string.buffer = RingBuffer(len(values))
        for value in values:
            string.buffer.enqueue(value)
        return string

    def __len__(self):
        """Number of samples in the buffer. Provided."""
        return self.buffer.size()

    def pluck(self):
        half = self.buffer.__len__()//2

        for i in range(self.buffer.__len__()):
            self.buffer.dequeue()
            if i < half:
                self.buffer.enqueue(PLUCK_AMPLITUDE)
            else:
                self.buffer.enqueue(-PLUCK_AMPLITUDE)

    def next_sample(self):
        value1 = self.buffer.dequeue()
        value2 = self.buffer.peek()
        newvalue = DECAY*((1/2)*(value1+value2))
        self.buffer.enqueue(newvalue)
        return value1

    def energy(self):
        total = 0.0
        n = self.buffer.size()
        for _ in range(n):
            value = self.buffer.dequeue()
            total += abs(value)
            self.buffer.enqueue(value)
        return total / n


