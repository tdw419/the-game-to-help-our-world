


# --- 4. CommandHistory Class ---
class CommandHistory:
    """Manages the history of entered commands."""
    def __init__(self) -> None:
        self.history: List[str] = []
        self.index: int = -1 # Points to the command currently in the entry, or end of history

    def add_command(self, cmd: str) -> None:
        """Adds a command to history and resets index."""
        if cmd and (not self.history or self.history[-1] != cmd): # Avoid duplicate consecutive commands
            self.history.append(cmd)
        self.index = len(self.history) # Set index to point after last command

    def get_previous(self) -> Optional[str]:
        """Gets the previous command in history."""
        if self.index > 0:
            self.index -= 1
            return self.history[self.index]
        return None

    def get_next(self) -> Optional[str]:
        """Gets the next command in history."""