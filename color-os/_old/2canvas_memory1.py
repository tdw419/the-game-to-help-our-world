from typing import List, Tuple, Optional, NamedTuple
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class DrawAction:
    """Immutable representation of a drawing action."""
    x: int
    y: int
    char: str
    color: str
    
    def adjust_y(self, offset: int) -> 'DrawAction':
        """Returns a new DrawAction with adjusted y-coordinate."""
        return DrawAction(self.x, self.y + offset, self.char, self.color)


class MemoryManager:
    """
    Manages the history of drawn characters with efficient undo/redo functionality.
    
    Uses separate data structures for current state vs undo/redo history to avoid
    data duplication and improve performance.
    """
    
    def __init__(self, max_size: int = 1000) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be positive")
            
        self.max_size = max_size
        
        # Current state - all visible characters
        self._memory: List[DrawAction] = []
        
        # Undo/redo stacks using deque for O(1) operations
        self._undo_stack: deque[DrawAction] = deque(maxlen=max_size)
        self._redo_stack: deque[DrawAction] = deque(maxlen=max_size)
    
    def add_action(self, x: int, y: int, char: str, color: str) -> None:
        """
        Adds a new drawing action to memory and enables undo functionality.
        
        Args:
            x: X coordinate
            y: Y coordinate  
            char: Character to draw
            color: Color of the character
        """
        action = DrawAction(x, y, char, color)
        
        # Add to current memory
        self._memory.append(action)
        
        # Add to undo stack for potential undoing
        self._undo_stack.append(action)
        
        # Clear redo stack since new action invalidates redo history
        self._redo_stack.clear()
        
        # Maintain memory size limit
        self._limit_memory_size()
    
    def undo(self) -> Optional[DrawAction]:
        """
        Undoes the last action by removing it from memory.
        
        Returns:
            The undone action if successful, None if nothing to undo
        """
        if not self._undo_stack:
            return None
            
        # Get the last action from undo stack
        last_action = self._undo_stack.pop()
        
        # Remove from current memory (search from end for efficiency)
        for i in range(len(self._memory) - 1, -1, -1):
            if self._memory[i] == last_action:
                self._memory.pop(i)
                break
        
        # Add to redo stack
        self._redo_stack.append(last_action)
        
        return last_action
    
    def redo(self) -> Optional[DrawAction]:
        """
        Redoes the last undone action.
        
        Returns:
            The redone action if successful, None if nothing to redo
        """
        if not self._redo_stack:
            return None
            
        # Get action from redo stack
        action = self._redo_stack.pop()
        
        # Add back to memory and undo stack
        self._memory.append(action)
        self._undo_stack.append(action)
        
        return action
    
    def get_all_actions(self) -> List[DrawAction]:
        """Returns a copy of all current drawing actions."""
        return self._memory.copy()
    
    def get_actions_in_area(self, min_x: int, max_x: int, min_y: int, max_y: int) -> List[DrawAction]:
        """
        Returns actions within the specified rectangular area.
        
        Args:
            min_x, max_x: X coordinate bounds (inclusive)
            min_y, max_y: Y coordinate bounds (inclusive)
            
        Returns:
            List of actions within the specified area
        """
        return [
            action for action in self._memory
            if min_x <= action.x <= max_x and min_y <= action.y <= max_y
        ]
    
    def clear_all(self) -> None:
        """Clears all memory and undo/redo history."""
        self._memory.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def clear_area(self, min_x: int, max_x: int, min_y: int, max_y: int) -> int:
        """
        Clears all actions within the specified area.
        
        Returns:
            Number of actions removed
        """
        initial_count = len(self._memory)
        
        self._memory = [
            action for action in self._memory
            if not (min_x <= action.x <= max_x and min_y <= action.y <= max_y)
        ]
        
        return initial_count - len(self._memory)
    
    def adjust_for_scroll(self, y_offset: int, visible_min_y: int, visible_max_y: int) -> None:
        """
        Adjusts coordinates after scrolling and removes off-screen actions.
        
        Args:
            y_offset: Amount to adjust y-coordinates
            visible_min_y: Minimum visible y-coordinate after adjustment
            visible_max_y: Maximum visible y-coordinate after adjustment
        """
        adjusted_memory = []
        
        for action in self._memory:
            adjusted_action = action.adjust_y(y_offset)
            
            # Keep only actions within visible area (with some buffer)
            if visible_min_y <= adjusted_action.y <= visible_max_y:
                adjusted_memory.append(adjusted_action)
        
        self._memory = adjusted_memory
    
    def can_undo(self) -> bool:
        """Returns True if undo is possible."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Returns True if redo is possible."""
        return len(self._redo_stack) > 0
    
    def get_stats(self) -> dict:
        """Returns statistics about current memory usage."""
        return {
            'memory_count': len(self._memory),
            'undo_available': len(self._undo_stack),
            'redo_available': len(self._redo_stack),
            'max_size': self.max_size,
            'memory_usage_percent': (len(self._memory) / self.max_size) * 100
        }
    
    def _limit_memory_size(self) -> None:
        """Maintains memory size within limits by removing oldest entries."""
        if len(self._memory) > self.max_size:
            # Remove oldest entries
            excess = len(self._memory) - self.max_size
            self._memory = self._memory[excess:]
    
    def __len__(self) -> int:
        """Returns the number of actions in memory."""
        return len(self._memory)
    
    def __bool__(self) -> bool:
        """Returns True if there are any actions in memory."""
        return len(self._memory) > 0