# cursor.py

from typing import Tuple

# Assuming these are defined elsewhere or you will define them
class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class CanvasBounds:
    def __init__(self, left: int, top: int, right: int, bottom: int):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

class CursorController:
    def __init__(self, start_position: Position, char_width: int, char_height: int,
                 canvas_bounds: CanvasBounds, initial_column: int = 0, initial_line: int = 0) -> None:
        self.start_position = start_position
        self.char_width = char_width
        self.char_height = char_height
        self.canvas_bounds = canvas_bounds

        self.current_column = initial_column
        self.current_line = initial_line
        
        # New attributes to store canvas dimensions in terms of columns and lines
        self.max_columns: int = 0
        self.max_lines: int = 0

    def set_canvas_dimensions(self, columns: int, lines: int) -> None:
        """Sets the maximum columns and lines for cursor movement."""
        self.max_columns = columns
        self.max_lines = lines

    def get_pixel_coords(self) -> Tuple[int, int]:
        """Calculates the pixel coordinates for the current cursor position."""
        x = self.start_position.x + (self.current_column * self.char_width)
        y = self.start_position.y + (self.current_line * self.char_height)
        return (x, y)

    def set_position_by_line_col(self, line: int, column: int) -> None:
        """Sets the cursor position by line and column, clamping to bounds."""
        self.current_line = max(0, min(line, self.max_lines - 1 if self.max_lines > 0 else line))
        self.current_column = max(0, min(column, self.max_columns - 1 if self.max_columns > 0 else column))

    def move_right(self) -> None:
        """Moves the cursor one character to the right."""
        self.current_column += 1
        if self.current_column >= self.max_columns and self.max_columns > 0:
            self.current_column = self.max_columns - 1 # Stay at end of line if max_columns is set

    def move_left(self) -> None:
        """Moves the cursor one character to the left."""
        self.current_column = max(0, self.current_column - 1)

    def move_up(self) -> None:
        """Moves the cursor one line up."""
        self.current_line = max(0, self.current_line - 1)

    def move_down(self) -> None:
        """Moves the cursor one line down."""
        self.current_line = min(self.max_lines - 1 if self.max_lines > 0 else self.current_line + 1, self.current_line + 1)


    def move_to_next_line(self) -> None:
        """Moves the cursor to the beginning of the next line."""
        self.current_line += 1
        self.current_column = 0
        # No clamping here, as the terminal canvas handles scrolling if it goes out of bounds

    def move_to_column(self, column: int) -> None:
        """Moves the cursor to a specific column on the current line."""
        self.current_column = max(0, min(column, self.max_columns - 1 if self.max_columns > 0 else column))

    def reset_position(self) -> None:
        """Resets the cursor to its initial position (0,0)."""
        self.current_column = 0
        self.current_line = 0