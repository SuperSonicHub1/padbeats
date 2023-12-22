from collections import deque
import time

from clockblocks import Clock


class MIDIClock:
    """
    Syncs clock of a MIDI clock master to a clockblocks.Clock.
    Based on https://github.com/SpotlightKid/python-rtmidi/blob/f762d4d752f08493c6c0e90d8f4e48fb35308a14/examples/advanced/midiclock.py
    24 clocks = 1 quarter note
    http://personal.kent.edu/~sbirch/Music_Production/MP-II/MIDI/midi_system_real.htm
    """  # noqa: E501

    bpm: float
    clock: Clock
    _samples: deque[float]
    _last_clock: float

    def __init__(self):
        # TODO: Are these useful?
        # self.sync = False
        # self.running = True
        self.bpm = 120.
        self.clock = Clock(initial_tempo=self.bpm)
        self._samples = deque(maxlen=24)
        self._last_clock = None

    def __call__(self, message):
        """
        Determination of the BPM is a bit janky ATM, but that can be fixed!
        """
        match message.type:
            case 'clock':
                now = time.time()
                if self._last_clock is not None:
                    self._samples.append(now - self._last_clock)

                self._last_clock = now

                if len(self._samples) >= 2:
                    self.bpm = 2.5 / (sum(self._samples) / len(self._samples))
                    self.clock.tempo = self.bpm
                    # self.sync = True
            case 'start':
                self.clock.release_from_suspension()
                # self.running = True
                # print("START received.")
            case 'continue':
                self.clock.release_from_suspension()
                # self.running = True
                # print("CONTINUE received.")
            case 'stop':
                self.clock.rouse_and_hold()
                # print("STOP received.")


if __name__ == "__main__":
    from .midi_util import open_midi_input

    clock = MIDIClock()
    m_in = open_midi_input()
    m_in.callback = clock

    with m_in:
        try:
            print("Waiting for clock sync...")
            while True:
                clock.clock.wait(1, units="time")
                print("%.2f bpm" % clock.bpm)
        except KeyboardInterrupt:
            pass
