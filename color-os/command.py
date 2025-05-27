# command.py

from typing import List, Optional
import enum

# Assuming HistoryMode is defined elsewhere, if not, you'll need to define it
class HistoryMode(enum.Enum):
    NAVIGATING = 1
    EDITING = 2

class CommandHistory:
    def __init__(self, capacity: int = 50) -> None:
        self.history: List[str] = []
        self.capacity = capacity # Store the capacity
        self.current_index: int = -1
        self.mode = HistoryMode.NAVIGATING

    def add_command(self, command: str) -> None:
        if command and (not self.history or self.history[-1] != command):
            if len(self.history) >= self.capacity:
                self.history.pop(0) # Remove the oldest command if capacity is exceeded
            self.history.append(command)
        self._reset_navigation() # Reset index after adding a new command

    def get_previous(self) -> Optional[str]:
        if not self.history:
            return None
        
        if self.current_index == -1: # Starting from the most recent command
            self.current_index = len(self.history) - 1
        elif self.current_index > 0:
            self.current_index -= 1
        else:
            return None # Already at the oldest command

        return self.history[self.current_index]

    def get_next(self) -> Optional[str]:
        if not self.history or self.current_index == -1:
            return None
        
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        else:
            self._reset_navigation() # Reached the end of history, clear input
            return "" # Return empty string to clear the input field

    def _reset_navigation(self) -> None:
        self.current_index = -1
        self.mode = HistoryMode.NAVIGATING

    def clear(self) -> None:
        self.history = []
        self.current_index = -1
        self.mode = HistoryMode.NAVIGATING