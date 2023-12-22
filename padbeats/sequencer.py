from fractions import Fraction
from math import floor
from threading import Thread
from typing import Literal

import numpy as np
from mido import Message
from mido.ports import BaseInput, BaseOutput

from .midi_util import open_midi_input, open_midi_output

INSTRUMENT_NAME = "PadBeats"

WIDTH = 8
HEIGHT = 6

# https://en.wikipedia.org/wiki/General_MIDI#Percussion
DEFAULT_NOTE_MAP = (
    36,  # Electric Bass Drum
    40,  # Acoustic Snare
    39,  # Hand Clap
    42,  # Hat Closed
    46,  # Hat Open
    51,  # Ride Cymbal 1
)


def do_notes(
    out: BaseOutput,
    msg: Literal['note_on'] | Literal['note_off'],
    notes: list[tuple[int, int | None]],
    channel: int = 0,
) -> None:
    for note, velocity in notes:
        out.send(
            Message(msg, note=note, velocity=velocity or 127, channel=channel)
        )


NoteMap = tuple[int, int, int, int, int, int]

class Sequencer:
    midi_in: BaseInput
    midi_out: BaseOutput
    beat_matrix: np.ndarray
    note_map: NoteMap
    quarter_notes: Fraction
    clock_running: bool

    def __init__(
        self,
        midi_in: BaseInput,
        midi_out: BaseOutput,
        note_map: NoteMap = DEFAULT_NOTE_MAP
    ):
        self.quarter_notes = Fraction()
        self.clock_running = True

        self.beat_matrix = np.asarray(
           [[1., 1., 1., 1., 1., 1., 1., 1.,],
            [0., 0., 0., 0., 0., 0., 0., 0.,],
            [0., 0., 0., 0., 0., 0., 0., 0.,],
            [0., 0., 0., 0., 0., 0., 0., 0.,],
            [0., 0., 0., 0., 0., 0., 0., 0.,],
            [1., 1., 1., 1., 1., 1., 1., 1.,],]
        )
        # np.ones((HEIGHT, WIDTH), dtype=np.float64)
        self.note_map = note_map

        self.midi_in = midi_in
        self.midi_out = midi_out
        self.midi_in.callback = self.handle_clock

    def handle_clock(self, message):
        """
        Listens to Timing Clock messages and keeps track of how much time has passed.
        24 clocks = 1 quarter note
        http://personal.kent.edu/~sbirch/Music_Production/MP-II/MIDI/midi_system_real.htm
        """
        match message.type:
            case 'clock':
                if self.clock_running:
                    self.quarter_notes += Fraction(1, 24)
                    # HACK: Allow for time signatures other than X/4
                    if self.quarter_notes.denominator == 1:
                        beat = int(self.quarter_notes % 8)
                        # do_notes(
                        #     self.midi_out,
                        #     'note_off',
                        #     [
                        #         (self.note_map[track], 112)
                        #         for track in range(HEIGHT)
                        #         if self.beat_matrix[track][beat - 1]
                        #     ],
                        #     length=1,
                        #     channel=9
                        # )
                        do_notes(
                            self.midi_out,
                            'note_on',
                            [
                                (self.note_map[track], 112)
                                for track in range(HEIGHT)
                                if self.beat_matrix[track][beat]
                            ],
                            channel=9
                        )
            case 'start':
                self.clock_running = True
                self.quarter_notes = Fraction()
            case 'continue':
                self.clock_running = True
            case 'stop':
                self.clock_running = False

    def measure(self, time_sig: Fraction = Fraction(4, 4)):
        quarter_notes_in_measure = time_sig * 4
        return floor(self.quarter_notes / quarter_notes_in_measure) + 1

    def beat(self, time_sig: Fraction = Fraction(4, 4)):
        quarter_notes_in_measure = time_sig * 4
        return floor(self.quarter_notes % quarter_notes_in_measure) + 1

    def run(self):
        time_sig = Fraction(8, 4)
        while True:
            print(self.measure(time_sig), self.beat(time_sig))

if __name__ == "__main__":
    midi_in = open_midi_input()
    midi_out = open_midi_output()

    sequencer = Sequencer(midi_in, midi_out)
    thread = Thread(target=sequencer.run)
    thread.run()
