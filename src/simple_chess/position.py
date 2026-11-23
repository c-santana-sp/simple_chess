from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int  # from 0..7
    col: int  # from 0..7 (a..h)
