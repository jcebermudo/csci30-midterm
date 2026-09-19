from array import array


class RingBuffer:

    def __init__(self, capacity):

        if capacity < 1:
            raise ValueError("Capacity is less than 1")
        
        self._data = array("d", [0.0]*capacity)
        self._front = 0
        self._rear = 0
        self._size = 0

    def capacity(self):
        return len(self._data)

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def is_full(self):
        return self._size == self.capacity() 

    def enqueue(self, x):
        if self.is_full():
            raise IndexError("Queue Full")
        else:
            self._data[self._rear] = x
            self._rear = (self._rear + 1) % self.capacity()
            self._size += 1

    def dequeue(self):
        """Remove and return the item at the front. 

        Raise IndexError if the buffer is empty.
        """
        if self.is_empty():
            raise IndexError("Queue Empty")
        else:
            to_return = self._data[self._front]
            self._front = (self._front + 1) % self.capacity()
            self._size -= 1
            return to_return

    def peek(self):
        if self.is_empty():
            raise IndexError("Queue Empty")
        return self._data[self._front]

    def __len__(self):
        """So that len(buffer) works. Provided, once size() works."""
        return self.size()
