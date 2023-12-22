import mido
from mido.ports import BaseInput, BaseOutput


def open_midi_input() -> BaseInput:
    """
    Interactively pick input from terminal.
    """
    names = mido.get_input_names()
    for i, name in enumerate(names):
        print(f"{i}: {name}")
    return mido.open_input(names[int(input("> "))])


def open_midi_output() -> BaseOutput:
    """
    Interactively pick output from terminal.
    """
    names = mido.get_output_names()
    for i, name in enumerate(names):
        print(f"{i}: {name}")
    return mido.open_output(names[int(input("> "))])
