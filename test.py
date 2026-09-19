from tonematrix.string_instrument import StringInstrument
from tonematrix.audio import write_wav

string = StringInstrument(750.0)
string.pluck()
write_wav("one_note.wav", [string.next_sample() for i in range(44100 * 3)])