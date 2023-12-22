"""
Receive MIDI clock and print out current BPM.
MIDI clock (status 0xF8) is sent 24 times per quarter note by clock generators.
"""

import argparse
from collections import deque
import time

import mido
from mido.ports import BaseInput, BaseOutput

# from rtmidi.midiconstants import (TIMING_CLOCK, SONG_CONTINUE, SONG_START, SONG_STOP)
# from rtmidi.midiutil import open_midiinput


def open_midi_input() -> BaseInput:
    names = mido.get_input_names()
    for i, name in enumerate(names):
        print(f"{i}: {name}")
    return mido.open_input(names[int(input("> "))])


def open_midi_output() -> BaseOutput:
    names = mido.get_output_names()
    for i, name in enumerate(names):
        print(f"{i}: {name}")
    return mido.open_output(names[int(input("> "))])


class MIDIClockReceiver:
    def __init__(self, bpm=None):
        self.bpm = bpm if bpm is not None else 120.0
        self.sync = False
        self.running = True
        self._samples = deque()
        self._last_clock = None

    def __call__(self, message):
        """
        Determination of the BPM is a bit janky ATM, but that can be fixed!
        """
        # print(message)
        match message.type:
            case 'clock':
                now = time.time()
                if self._last_clock is not None:
                    self._samples.append(now - self._last_clock)

                self._last_clock = now

                if len(self._samples) > 24:
                    self._samples.popleft()

                if len(self._samples) >= 2:
                    self.bpm = 2.5 / (sum(self._samples) / len(self._samples))
                    self.sync = True
            case 'start':
                self.running = True
                print("START received.")
            case 'continue':
                self.running = True
                print("CONTINUE received.")
            case 'stop':
                self.running = False
                print("STOP received.")


def main():
    ap = argparse.ArgumentParser(usage=__doc__.splitlines()[0])
    ap.add_argument('bpm', type=int, default=120, help="Starting BPM.")
    args = ap.parse_args()

    clock = MIDIClockReceiver(args.bpm)

    try:
        m_in = open_midi_input()
    except (EOFError, KeyboardInterrupt):
        return 1

    m_in.callback = clock

    with m_in:
        try:
            print("Waiting for clock sync...")
            while True:
                time.sleep(1)
                if clock.running:
                    if clock.sync:
                        print("%.2f bpm" % clock.bpm)
                    else:
                        print("%.2f bpm (no sync)" % clock.bpm)

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    import sys
    sys.exit(main() or 0)
