from typing import List, Optional, Iterator, Set
from collections import deque
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime


class HistoryMode(Enum):
    """History navigation modes."""
    SEQUENTIAL = "sequential"  # Navigate through all commands in order
    FILTERED = "filtered"      # Navigate through filtered/searched commands only


@dataclass
class HistoryEntry:
    """Represents a single command history entry."""
    command: str
    timestamp: datetime
    execution_count: int = 1
    
    def __str__(self) -> str:
        return self.command
    
    def __eq__(self, other) -> bool:
        if isinstance(other, HistoryEntry):
            return self.command == other.command
        elif isinstance(other, str):
            return self.command == other
        return False


class CommandHistory:
    """
    Advanced command history manager with search, filtering, and persistence capabilities.
    
    Features:
    - Configurable history size limits
    - Duplicate handling with execution counting
    - Command search and filtering
    - History navigation with different modes
    - Statistics and analytics
    - Import/export capabilities
    """
    
    def __init__(
        self, 
        max_size: int = 1000,
        allow_duplicates: bool = False,
        case_sensitive: bool = True,
        trim_whitespace: bool = True
    ) -> None:
        if not isinstance(max_size, int) or max_size <= 0:
            raise ValueError("max_size must be a positive integer.")
        
        self._history: deque[HistoryEntry] = deque(maxlen=max_size)
        self._max_size = max_size
        self._allow_duplicates = allow_duplicates
        self._case_sensitive = case_sensitive
        self._trim_whitespace = trim_whitespace
        
        # Navigation state
        self._current_index: int = -1 # -1 means no command selected, or after history
        self._temp_command: Optional[str] = None # Stores command typed before history navigation
        
        # Filter state
        self._mode: HistoryMode = HistoryMode.SEQUENTIAL
        self._filtered_indices: List[int] = [] # Indices of commands matching current filter
        self._last_search_query: Optional[str] = None

    def add_command(self, command: str) -> None:
        """
        Adds a command to the history. Handles duplicates if configured.
        Resets navigation state upon adding a new command.
        """
        if self._trim_whitespace:
            command = command.strip()
        
        if not command:
            return # Don't add empty commands

        # Reset navigation whenever a new command is added
        self._reset_navigation()
        
        if not self._allow_duplicates:
            # Check for existing command (case-insensitive if configured)
            found_existing = False
            for i, entry in enumerate(self._history):
                if self._commands_equal(entry.command, command):
                    entry.execution_count += 1
                    # Move to end to simulate "recently used" if it's not already there
                    if i != len(self._history) - 1:
                        # Remove and re-add to move to end of deque
                        temp_deque = deque(maxlen=self._max_size)
                        for j, val in enumerate(self._history):
                            if j != i:
                                temp_deque.append(val)
                        self._history = temp_deque
                        self._history.append(entry)
                    found_existing = True
                    break
            
            if not found_existing:
                self._history.append(HistoryEntry(command=command, timestamp=datetime.now()))
        else:
            self._history.append(HistoryEntry(command=command, timestamp=datetime.now()))
        
        # Rebuild filtered indices if a search is active
        if self._mode == HistoryMode.FILTERED and self._last_search_query:
            self.search(self._last_search_query, regex=True if self._last_search_query.startswith('/') else False)

    def get_previous(self) -> Optional[str]:
        """Navigates to the previous command in history."""
        if self._mode == HistoryMode.SEQUENTIAL:
            if self._current_index == -1: # Just started navigating, go to last
                if self._history:
                    self._current_index = len(self._history) - 1
                else:
                    return None # No history available
            elif self._current_index > 0:
                self._current_index -= 1
            else:
                return None # Already at the beginning of history
            return self._history[self._current_index].command
        else: # FILTERED mode
            try:
                # If _current_index is -1, it means we are 'after' the last filtered command.
                # Find the position of _current_index in _filtered_indices.
                # If _current_index is -1, start from the end of filtered_indices to go back.
                current_filtered_pos = self._filtered_indices.index(self._current_index) if self._current_index != -1 else len(self._filtered_indices)

                if current_filtered_pos > 0:
                    filtered_pos = current_filtered_pos - 1
                    self._current_index = self._filtered_indices[filtered_pos]
                    return self._history[self._current_index].command
                else:
                    return None # Already at beginning of filtered results
            except ValueError: # _current_index not found in _filtered_indices (e.g., first navigation in filtered mode)
                if self._filtered_indices:
                    self._current_index = self._filtered_indices[-1] # Go to the last filtered command
                    return self._history[self._current_index].command
                return None # No filtered history


    def get_next(self) -> Optional[str]:
        """Navigates to the next command in history."""
        if self._mode == HistoryMode.SEQUENTIAL:
            if self._current_index == -1: # After history, or no history
                return None # No next command, or already after history
            elif self._current_index < len(self._history) - 1:
                self._current_index += 1
                return self._history[self._current_index].command
            else:
                # Returned to "after history" state
                self._current_index = -1
                temp = self._temp_command
                self._temp_command = None
                return temp # Return temp command if stored, otherwise None
        else: # FILTERED mode
            try:
                # If _current_index is -1, it means we are 'after' the last filtered command or before the first.
                # If it's -1 and we are going 'next', it means we are trying to go beyond the last filtered command.
                current_filtered_pos = self._filtered_indices.index(self._current_index) if self._current_index != -1 else -1 # If not in filtered, assume before start

                if current_filtered_pos < len(self._filtered_indices) - 1:
                    filtered_pos = current_filtered_pos + 1
                    self._current_index = self._filtered_indices[filtered_pos]
                    return self._history[self._current_index].command
                else:
                    # Returned to "after filtered history" state
                    self._current_index = -1
                    temp = self._temp_command
                    self._temp_command = None
                    return temp # Return temp command if stored, otherwise None
            except ValueError: # _current_index not found in _filtered_indices
                # This could happen if _current_index was reset or never set in filtered mode
                if self._filtered_indices:
                    self._current_index = self._filtered_indices[0] # Go to the first filtered command
                    return self._history[self._current_index].command
                return None # No filtered history


    def search(self, query: str, regex: bool = False) -> List[HistoryEntry]:
        """
        Searches the history for commands matching the query.
        Sets the history mode to FILTERED and prepares for navigation.
        """
        self._last_search_query = query
        self._mode = HistoryMode.FILTERED
        self._filtered_indices = []
        self._current_index = -1 # Reset navigation for new search

        query_normalized = query if self._case_sensitive else query.lower()

        for i, entry in enumerate(self._history):
            command_to_match = entry.command if self._case_sensitive else entry.command.lower()
            
            match = False
            if regex:
                try:
                    if re.search(query_normalized, command_to_match):
                        match = True
                except re.error:
                    # Fallback to substring search if regex is invalid
                    if query_normalized in command_to_match:
                        match = True
            else:
                if query_normalized in command_to_match:
                    match = True
            
            if match:
                self._filtered_indices.append(i)
        
        return [self._history[idx] for idx in self._filtered_indices]

    def reset_search(self) -> None:
        """Resets the history navigation mode to SEQUENTIAL."""
        self._mode = HistoryMode.SEQUENTIAL
        self._filtered_indices = []
        self._last_search_query = None
        self._reset_navigation() # Reset navigation for sequential mode

    def _commands_equal(self, cmd1: str, cmd2: str) -> bool:
        """Compares two commands based on case sensitivity setting."""
        if not self._case_sensitive:
            return cmd1.lower() == cmd2.lower()
        return cmd1 == cmd2
    
    def _reset_navigation(self) -> None:
        """Resets navigation state."""
        self._current_index = -1
        self._temp_command = None
    
    def __len__(self) -> int:
        """Returns the number of commands in history."""
        return len(self._history)
    
    def __bool__(self) -> bool:
        """Returns True if history contains commands."""
        return len(self._history) > 0
    
    def __iter__(self) -> Iterator[HistoryEntry]:
        """Allows iteration over history entries."""
        return iter(self._history)
    
    def __getitem__(self, index: int) -> HistoryEntry:
        """Allows indexing into history."""
        if isinstance(index, slice):
            return list(self._history)[index] # Return a list for slices
        else:
            return self._history[index]

    def clear(self) -> None:
        """Clears all command history."""
        self._history.clear()
        self._reset_navigation()
        self.reset_search()

    def get_all_commands(self) -> List[str]:
        """Returns a list of all commands in history."""
        return [entry.command for entry in self._history]

    def get_statistics(self) -> Dict[str, Any]:
        """Returns statistics about the command history."""
        total_commands = len(self._history)
        unique_commands = len({entry.command for entry in self._history})
        total_executions = sum(entry.execution_count for entry in self._history)
        
        most_frequent: Optional[HistoryEntry] = None
        if self._history:
            most_frequent = max(self._history, key=lambda entry: entry.execution_count)

        return {
            "total_commands_stored": total_commands,
            "unique_commands": unique_commands,
            "total_executions": total_executions,
            "max_history_size": self._max_size,
            "allow_duplicates": self._allow_duplicates,
            "case_sensitive": self._case_sensitive,
            "most_frequent_command": most_frequent.command if most_frequent else None,
            "most_frequent_count": most_frequent.execution_count if most_frequent else 0
        }

    def save_to_file(self, filename: str) -> None:
        """Saves history to a file (one command per line)."""
        with open(filename, 'w', encoding='utf-8') as f:
            for entry in self._history:
                f.write(f"{entry.command}\n")

    def load_from_file(self, filename: str) -> None:
        """Loads history from a file."""
        if not self._allow_duplicates:
            print("Warning: Loading from file with allow_duplicates=False may skip existing commands.")
        
        temp_history: deque[HistoryEntry] = deque(maxlen=self._max_size)
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                command = line.strip()
                if command:
                    # For loaded commands, set timestamp to now and count to 1
                    entry = HistoryEntry(command=command, timestamp=datetime.now(), execution_count=1)
                    if not self._allow_duplicates:
                        # Check if command already exists in temp_history
                        if not any(self._commands_equal(e.command, command) for e in temp_history):
                            temp_history.append(entry)
                    else:
                        temp_history.append(entry)
        
        self._history = temp_history
        self._reset_navigation()
        self.reset_search()