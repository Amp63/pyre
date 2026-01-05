from abc import ABC, abstractmethod
from typing import Any


class CodeItem(ABC):
    type = '_codeitem'

    def __init__(self, slot: int|None):
        self.slot = slot

    @abstractmethod
    def format(self, slot: int|None) -> dict[str, dict[str, Any]]:
        """
        Returns a dictionary containing this code item's data formatted
        for a DF template JSON.
        """


def add_slot(d: dict, slot: int|None):
    if slot is not None:
        d['slot'] = slot
