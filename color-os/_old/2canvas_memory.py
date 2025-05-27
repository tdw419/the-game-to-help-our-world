# --- 2. MemoryManager Class ---
class MemoryManager:
    """Manages the history of drawn characters and undo/redo stacks."""
    def __init__(self, max_size: int) -> None:
        self.memory: List[Tuple[int, int, str, str]] = []
        self.undo_stack: List[Tuple[int, int, str, str]] = []
        self.redo_stack: List[Tuple[int, int, str, str]] = []
        self.max_size = max_size

    def add_action(self, x: int, y: int, char: str, color: str) -> None:
        """Adds a new character action to memory and undo stack."""
        self.memory.append((x, y, char, color))
        self.undo_stack.append((x, y, char, color))
        self.redo_stack.clear() # Any new action clears the redo stack
        self.limit_stacks()

    def pop_last_action(self) -> Optional[Tuple[int, int, str, str]]:
        """Removes and returns the last action from memory."""
        if self.memory:
            return self.memory.pop()
        return None

    def push_to_redo(self, action: Tuple[int, int, str, str]) -> None:
        """Pushes an action to the redo stack."""
        self.redo_stack.append(action)
        self.limit_stacks()

    def pop_from_redo(self) -> Optional[Tuple[int, int, str, str]]:
        """Pops and returns an action from the redo stack."""
        if self.redo_stack:
            return self.redo_stack.pop()
        return None

    def add_to_memory(self, action: Tuple[int, int, str, str]) -> None:
        """Adds an action back to memory (e.g., during redo)."""
        self.memory.append(action)

    def get_all_memory(self) -> List[Tuple[int, int, str, str]]:
        """Returns all stored character actions."""
        return self.memory

    def clear_all(self) -> None:
        """Clears all memory and stacks."""
        self.memory.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def limit_stacks(self) -> None:
        """Limits the size of memory and undo/redo stacks."""
        if len(self.memory) > self.max_size:
            self.memory = self.memory[-self.max_size:]
        if len(self.undo_stack) > self.max_size:
            self.undo_stack = self.undo_stack[-self.max_size:]
        if len(self.redo_stack) > self.max_size:
            self.redo_stack = self.redo_stack[-self.max_size:]

    def adjust_memory_for_scroll(self, offset_y: int, min_y_visible: int) -> None:
        """Adjusts y-coordinates in memory after a scroll, removing off-screen items."""
        new_memory = []
        for x, y, char, color in self.memory:
            adjusted_y = y + offset_y
            if adjusted_y >= min_y_visible: # Only keep items that remain visible or just enter view
                new_memory.append((x, adjusted_y, char, color))
        self.memory = new_memory